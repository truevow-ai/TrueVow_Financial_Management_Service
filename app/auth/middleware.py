"""
Financial Management Authentication Middleware
Validates JWT tokens and checks service access
"""

from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from jose import jwt, JWTError
from app.core.config import settings
from app.core.logging import logger

security = HTTPBearer()


async def validate_token(token: str) -> dict:
    """
    Validate JWT token with centralized auth service.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Option 1: Validate with auth service (if configured)
        if hasattr(settings, 'auth_service_url') and settings.auth_service_url:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.auth_service_url}/api/v1/auth/validate",
                    json={"token": token},
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        
        # Option 2: Validate locally (if secret available)
        if settings.jwt_secret_key:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return payload
        
        raise HTTPException(status_code=401, detail="Invalid token")
    
    except httpx.HTTPError as e:
        logger.error(f"Auth service error: {e}")
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


async def verify_fm_access(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verify user has access to financial management service.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        Token payload if access granted
        
    Raises:
        HTTPException: If no access
    """
    token = credentials.credentials
    payload = await validate_token(token)
    
    # Check if user has financial management service access
    services = payload.get("services", [])
    if "financial_management" not in services:
        logger.warning(f"User {payload.get('user_id')} attempted FM access without permission")
        raise HTTPException(
            status_code=403,
            detail="No access to financial management service. Contact administrator."
        )
    
    return payload


async def get_current_user(
    token_payload: dict = Depends(verify_fm_access)
) -> dict:
    """
    Get current authenticated user from token.
    
    Args:
        token_payload: Validated token payload
        
    Returns:
        User information
    """
    return {
        "user_id": token_payload.get("user_id"),
        "email": token_payload.get("email"),
        "roles": token_payload.get("roles", []),
        "permissions": token_payload.get("permissions", {}).get("financial_management", []),
    }


def check_fm_permission(
    user: dict,
    required_permission: str
) -> bool:
    """
    Check if user has required financial management permission.
    
    Args:
        user: Current user dict
        required_permission: Required permission (read, write, admin)
        
    Returns:
        True if user has permission
    """
    user_permissions = user.get("permissions", [])
    user_roles = user.get("roles", [])
    
    # Admin roles have all permissions
    if "admin" in user_roles or "finance_head" in user_roles:
        return True
    
    # Check specific permission
    if required_permission in user_permissions:
        return True
    
    # Admin permission grants all
    if "admin" in user_permissions:
        return True
    
    return False

