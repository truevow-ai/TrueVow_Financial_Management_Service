"""
TrueVow Security Contract v1 — AuthContext + JWKSManager

Section 4 — Centralized Auth Middleware contract:
  1. Generate request_id = uuid4() at entry
  2. Verify JWT locally via JWKS (auth_mode=clerk) or HS256 (auth_mode=local)
  3. Enforce scope (first gate after signature verification)
  4. Extract: sub, org_id, tenant_id, scope
  5. Load role + permissions from DB (NOT from JWT)
  6. Attach AuthContext to request
  7. Log auth audit event

Section 5 — AUTH_MODE guard:
  If ENV=production AND AUTH_MODE != "clerk" → RuntimeError at startup.

Section 1.1 — Canonical tenant identifier:
  tenant_id = Clerk org_id (TEXT).  Never UUID.

Scope declarations for this service (FM = Platform Core):
  FM_ALLOWED_SCOPES = ["internal", "tenant"]
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

import httpx
from jose import jwt as jose_jwt, jwk as jose_jwk, JWTError
from fastapi import HTTPException

from app.core.logging import logger


# ---------------------------------------------------------------------------
# AuthContext
# ---------------------------------------------------------------------------

@dataclass
class AuthContext:
    """
    Unified authentication context attached to request.state.auth_context
    after successful verification.

    Contract Section 4 — fields required:
      - request_id   : uuid4 generated at middleware entry
      - sub          : Clerk user ID (VARCHAR 255)
      - org_id       : Clerk org ID (TEXT) — canonical cross-service tenant ID
      - tenant_id    : = org_id (alias per contract Section 1.1)
      - scope        : "internal" | "tenant"
      - fm_role      : FM-specific role (from DB)
      - permissions  : List of resource:action strings (from DB, fail-CLOSED)
    """
    request_id: str                         # uuid4 generated at entry
    sub: str                                # Clerk user_id
    org_id: Optional[str]                   # Clerk org_id (TEXT)
    tenant_id: Optional[str]               # alias for org_id
    scope: str                              # "internal" | "tenant"
    email: Optional[str] = None
    fm_role: Optional[str] = None          # FM RBAC role from DB
    internal_role: Optional[str] = None   # TrueVow internal role
    permissions: List[str] = field(default_factory=list)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None

    def has_permission(self, permission: str) -> bool:
        """Check resource:action permission (contract Section 6.3)."""
        return permission in self.permissions or "*" in self.permissions

    def is_internal(self) -> bool:
        return self.scope == "internal"

    def is_tenant(self) -> bool:
        return self.scope == "tenant"


# ---------------------------------------------------------------------------
# JWKSManager — Clerk RS256 JWKS verification (auth_mode=clerk)
# ---------------------------------------------------------------------------

class JWKSManager:
    """
    Caches and rotates Clerk JWKS keys.

    Contract Section 4, item 2: Verify JWT locally via JWKS.
    Contract Section 5: Used only when auth_mode=clerk.

    Thread-safety: asyncio-safe via in-memory TTL cache.
    Concurrent JWKS fetches are serialised via _refreshing flag.
    """

    def __init__(self, jwks_url: str, cache_ttl: int = 3600):
        self._jwks_url = jwks_url
        self._cache_ttl = cache_ttl
        self._keys: Dict[str, Any] = {}         # kid → JWK
        self._fetched_at: float = 0.0
        self._refreshing: bool = False

    def _cache_valid(self) -> bool:
        return (
            bool(self._keys)
            and (time.monotonic() - self._fetched_at) < self._cache_ttl
        )

    async def _refresh(self) -> None:
        """Fetch fresh JWKS from Clerk endpoint."""
        if self._refreshing:
            return
        self._refreshing = True
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(self._jwks_url)
                resp.raise_for_status()
                data = resp.json()
            new_keys: Dict[str, Any] = {}
            for key_data in data.get("keys", []):
                kid = key_data.get("kid", "__default__")
                new_keys[kid] = key_data
            self._keys = new_keys
            self._fetched_at = time.monotonic()
            logger.info(f"JWKSManager: refreshed {len(new_keys)} keys from {self._jwks_url}")
        except Exception as exc:
            logger.error(f"JWKSManager: failed to refresh JWKS: {exc}")
            # Do NOT clear existing keys on refresh failure — stale is safer than empty.
        finally:
            self._refreshing = False

    def _get_signing_key(self, token: str) -> Any:
        """
        Extract JWK for the token's kid header.
        Returns the raw key dict for jose.jwk.construct().
        """
        try:
            headers = jose_jwt.get_unverified_header(token)
        except JWTError as exc:
            raise HTTPException(status_code=401, detail=f"Invalid token header: {exc}")

        kid = headers.get("kid", "__default__")
        key_data = self._keys.get(kid) or self._keys.get("__default__")
        if not key_data:
            raise HTTPException(
                status_code=401,
                detail=f"JWT kid '{kid}' not found in JWKS — possible key rotation",
            )
        return key_data

    async def verify(self, token: str) -> dict:
        """
        Full JWKS verification pipeline:
        1. Refresh cache if stale
        2. Locate signing key by kid
        3. Verify RS256 signature + expiry
        4. Return claims dict

        Raises HTTPException(401) on any failure.
        """
        if not self._cache_valid():
            await self._refresh()

        key_data = self._get_signing_key(token)
        try:
            public_key = jose_jwk.construct(key_data)
            claims = jose_jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
            return claims
        except JWTError as exc:
            # Try once more with a fresh key set in case of rotation
            await self._refresh()
            key_data = self._get_signing_key(token)
            try:
                public_key = jose_jwk.construct(key_data)
                claims = jose_jwt.decode(
                    token,
                    public_key,
                    algorithms=["RS256"],
                    options={"verify_aud": False},
                )
                return claims
            except JWTError:
                raise HTTPException(status_code=401, detail=f"JWT verification failed: {exc}")


# ---------------------------------------------------------------------------
# Module-level singleton (initialised lazily by authorization.py)
# ---------------------------------------------------------------------------

_jwks_manager: Optional[JWKSManager] = None


def get_jwks_manager() -> Optional[JWKSManager]:
    """Return the module-level JWKSManager singleton, or None for local mode."""
    return _jwks_manager


def init_jwks_manager(jwks_url: str, cache_ttl: int = 3600) -> JWKSManager:
    """Initialise the singleton. Called once at startup when auth_mode=clerk."""
    global _jwks_manager
    _jwks_manager = JWKSManager(jwks_url, cache_ttl)
    logger.info(f"JWKSManager initialised: url={jwks_url}, ttl={cache_ttl}s")
    return _jwks_manager
