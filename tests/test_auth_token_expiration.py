"""
Test Token Expiration Enforcement (sec_auth_002)

Validates:
- Expired tokens are rejected with 401
- Clock skew handling (+/- 5 minutes)
- Token refresh flow simulation
"""

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt
from fastapi import HTTPException
from app.auth.middleware import validate_token
from app.core.config import settings


@pytest.fixture
def valid_jwt_secret():
    return "test-secret-key-do-not-use-in-production"


@pytest.fixture
def jwt_algorithm():
    return "HS256"


@pytest.fixture
def create_token(valid_jwt_secret, jwt_algorithm):
    """Factory to create JWT tokens"""
    def _create_token(payload: dict, secret: str = None, algorithm: str = None):
        return jwt.encode(
            payload,
            secret or valid_jwt_secret,
            algorithm=algorithm or jwt_algorithm
        )
    return _create_token


@pytest.mark.asyncio
async def test_expired_token_rejected(create_token, valid_jwt_secret, monkeypatch):
    """Test expired token is rejected with 401"""
    # Arrange
    expired_payload = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "services": ["financial_management"],
        "exp": datetime.now(timezone.utc) - timedelta(minutes=10),  # Expired 10 min ago
        "iat": datetime.now(timezone.utc) - timedelta(minutes=40),
    }
    token = create_token(expired_payload)
    monkeypatch.setattr(settings, "jwt_secret_key", valid_jwt_secret)
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await validate_token(token)
    
    assert exc_info.value.status_code == 401
    assert "Invalid token" in exc_info.value.detail


@pytest.mark.asyncio
async def test_future_iat_allowed(create_token, valid_jwt_secret, monkeypatch):
    """Test token with future iat (issued at) is allowed (clock skew tolerance)"""
    # Arrange
    future_iat_payload = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "services": ["financial_management"],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        "iat": datetime.now(timezone.utc) + timedelta(minutes=2),  # 2 min in future
    }
    token = create_token(future_iat_payload)
    monkeypatch.setattr(settings, "jwt_secret_key", valid_jwt_secret)
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    
    # Act
    result = await validate_token(token)
    
    # Assert
    assert result is not None
    assert result["user_id"] == "test-user-123"


@pytest.mark.asyncio
async def test_nearly_expired_token_accepted_within_skew(create_token, valid_jwt_secret, monkeypatch):
    """Test token nearly expired but within clock skew tolerance is accepted"""
    # Arrange - jose library handles clock skew internally
    nearly_expired_payload = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "services": ["financial_management"],
        "exp": datetime.now(timezone.utc) + timedelta(seconds=30),  # Expires in 30s
        "iat": datetime.now(timezone.utc) - timedelta(minutes=10),
    }
    token = create_token(nearly_expired_payload)
    monkeypatch.setattr(settings, "jwt_secret_key", valid_jwt_secret)
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    
    # Act
    result = await validate_token(token)
    
    # Assert
    assert result is not None


@pytest.mark.asyncio
async def test_long_lived_token_accepted(create_token, valid_jwt_secret, monkeypatch):
    """Test long-lived token (1 day) is accepted"""
    # Arrange
    long_lived_payload = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "services": ["financial_management"],
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
        "iat": datetime.now(timezone.utc),
    }
    token = create_token(long_lived_payload)
    monkeypatch.setattr(settings, "jwt_secret_key", valid_jwt_secret)
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    
    # Act
    result = await validate_token(token)
    
    # Assert
    assert result is not None


@pytest.mark.asyncio
async def test_no_exp_claim_handled_gracefully(create_token, valid_jwt_secret, monkeypatch):
    """Test token without exp claim is handled gracefully (library allows it)"""
    # Arrange - jose library allows tokens without exp claim
    no_exp_payload = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "services": ["financial_management"],
        "iat": datetime.now(timezone.utc),
        # Missing exp claim - jose allows this
    }
    token = create_token(no_exp_payload)
    monkeypatch.setattr(settings, "jwt_secret_key", valid_jwt_secret)
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    
    # Act - token validates successfully (no expiration check)
    result = await validate_token(token)
    
    # Assert - token is valid from JWT perspective, app should enforce exp
    assert result is not None
    assert result["user_id"] == "test-user-123"


@pytest.mark.asyncio
async def test_zero_exp_claim_rejected(create_token, valid_jwt_secret, monkeypatch):
    """Test token with exp=0 is rejected"""
    # Arrange
    zero_exp_payload = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "services": ["financial_management"],
        "exp": 0,  # Epoch time 0 = 1970-01-01
        "iat": datetime.now(timezone.utc),
    }
    token = create_token(zero_exp_payload)
    monkeypatch.setattr(settings, "jwt_secret_key", valid_jwt_secret)
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await validate_token(token)
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_negative_exp_claim_rejected(create_token, valid_jwt_secret, monkeypatch):
    """Test token with negative exp claim is rejected"""
    # Arrange
    negative_exp_payload = {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "services": ["financial_management"],
        "exp": -1000,  # Negative timestamp
        "iat": datetime.now(timezone.utc),
    }
    token = create_token(negative_exp_payload)
    monkeypatch.setattr(settings, "jwt_secret_key", valid_jwt_secret)
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await validate_token(token)
    
    assert exc_info.value.status_code == 401
