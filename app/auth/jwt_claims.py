"""
JWT Claims Schema and Validation for Scope-Aware Auth Architecture
Version: 1.0.0

JWT Claim Schema v1.0.0:
{
  "iss": "https://clerk.truevow.com",
  "sub": "user_2abc123",
  "email": "john@truevow.com",
  
  "scope": "internal" | "tenant",
  "org_id": "org_abc123",
  
  // IF scope = "internal":
  "internal_role": "director",
  "internal_function": "platform",
  
  // IF scope = "tenant":
  "tenant_id": "tenant_abc123",
  "tenant_role": "admin"
}

Critical Rules:
1. Never mix scopes - JWT with both internal AND tenant claims is REJECTED
2. Never accept missing scope - JWT without scope is REJECTED
3. DB is source of truth - Permissions come from DB, not JWT
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from fastapi import HTTPException


class AuthScope(str, Enum):
    """Authentication scope types."""
    INTERNAL = "internal"
    TENANT = "tenant"


class JWTClaimsBase(BaseModel):
    """Base JWT claims present in all tokens."""
    iss: str = Field(..., description="Token issuer")
    sub: str = Field(..., description="Subject (user ID)")
    email: str = Field(..., description="User email")
    scope: AuthScope = Field(..., description="Authentication scope")
    org_id: Optional[str] = Field(None, description="Organization ID")
    iat: Optional[int] = Field(None, description="Issued at timestamp")
    exp: Optional[int] = Field(None, description="Expiration timestamp")


class InternalJWTClaims(JWTClaimsBase):
    """JWT claims for internal users (TrueVow employees)."""
    scope: AuthScope = AuthScope.INTERNAL
    internal_role: str = Field(..., description="Internal role (junior, senior, lead, manager, director, executive)")
    internal_function: Optional[str] = Field(None, description="Function (platform, finance, operations, etc.)")
    
    # Must NOT have tenant claims
    tenant_id: Optional[str] = Field(None, exclude=True)
    tenant_role: Optional[str] = Field(None, exclude=True)
    
    @field_validator('scope')
    @classmethod
    def validate_scope(cls, v):
        if v != AuthScope.INTERNAL:
            raise ValueError("Internal claims must have scope='internal'")
        return v
    
    @field_validator('internal_role')
    @classmethod
    def validate_role(cls, v):
        valid_roles = {'junior', 'senior', 'lead', 'manager', 'director', 'executive'}
        if v.lower() not in valid_roles:
            raise ValueError(f"Invalid internal_role: {v}. Must be one of {valid_roles}")
        return v.lower()


class TenantJWTClaims(JWTClaimsBase):
    """JWT claims for tenant users (Law Firm users)."""
    scope: AuthScope = AuthScope.TENANT
    tenant_id: str = Field(..., description="Tenant ID for data isolation")
    tenant_role: str = Field(..., description="Tenant role (viewer, member, admin, billing_admin)")
    
    # Must NOT have internal claims
    internal_role: Optional[str] = Field(None, exclude=True)
    internal_function: Optional[str] = Field(None, exclude=True)
    
    @field_validator('scope')
    @classmethod
    def validate_scope(cls, v):
        if v != AuthScope.TENANT:
            raise ValueError("Tenant claims must have scope='tenant'")
        return v
    
    @field_validator('tenant_role')
    @classmethod
    def validate_role(cls, v):
        valid_roles = {'viewer', 'member', 'admin', 'billing_admin'}
        if v.lower() not in valid_roles:
            raise ValueError(f"Invalid tenant_role: {v}. Must be one of {valid_roles}")
        return v.lower()


def validate_jwt_claims(claims: dict) -> JWTClaimsBase:
    """
    Validate JWT claims and return appropriate typed object.
    
    Args:
        claims: Raw JWT claims dictionary
        
    Returns:
        InternalJWTClaims or TenantJWTClaims based on scope
        
    Raises:
        HTTPException: If claims are invalid
    """
    # Rule 2: Never accept missing scope
    if 'scope' not in claims:
        raise HTTPException(
            status_code=401,
            detail="Invalid token: missing scope claim"
        )
    
    scope = claims.get('scope')
    
    # Rule 1: Never mix scopes
    has_internal = 'internal_role' in claims
    has_tenant = 'tenant_id' in claims or 'tenant_role' in claims
    
    if scope == 'internal':
        if has_tenant:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: internal scope cannot have tenant claims"
            )
        try:
            return InternalJWTClaims(**claims)
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid internal token: {str(e)}"
            )
    
    elif scope == 'tenant':
        if has_internal:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: tenant scope cannot have internal claims"
            )
        try:
            return TenantJWTClaims(**claims)
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid tenant token: {str(e)}"
            )
    
    else:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: unknown scope '{scope}'"
        )


@dataclass
class InternalUserContext:
    """Context for internal (TrueVow employee) users."""
    user_id: str
    email: str
    org_id: Optional[str]
    internal_role: str
    internal_function: Optional[str]
    
    # Permissions fetched from DB
    permissions: List[str] = None
    
    def is_internal(self) -> bool:
        return True
    
    def is_tenant(self) -> bool:
        return False
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.permissions is None:
            return False
        return permission in self.permissions or '*' in self.permissions


@dataclass
class TenantUserContext:
    """Context for tenant (Law Firm) users."""
    user_id: str
    email: str
    org_id: Optional[str]
    tenant_id: str
    tenant_role: str
    
    # Permissions fetched from DB
    permissions: List[str] = None
    
    def is_internal(self) -> bool:
        return False
    
    def is_tenant(self) -> bool:
        return True
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.permissions is None:
            return False
        return permission in self.permissions or '*' in self.permissions


# Type alias for union of user contexts
UserContext = InternalUserContext | TenantUserContext
