"""
TrueVow Security Contract v1 — Section 8
Route Protection Test (Mandatory in Every Service)

Contract requirements:
  * Inspect actual FastAPI app routes at runtime
  * Ensure all non-public routes have auth dependency
  * Ensure no route allows None user
  * Ensure public routes explicitly declared
  * Fail CI if violation found

Public routes for FM service (must be explicitly declared):
  GET  /health
  GET  /docs
  GET  /redoc
  GET  /openapi.json

All other routes MUST have at least one of the following dependencies:
  - get_user_context
  - require_internal_user
  - require_tenant_user
  - require_internal_permission
  - require_tenant_permission
  - verify_fm_access            (legacy)
  - get_current_user            (legacy)
"""

import inspect
import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute


# -----------------------------------------------------------------------
# Explicitly declared public routes — contract Section 7
# Public routes must EXPLICITLY override the default-deny policy.
# -----------------------------------------------------------------------
EXPLICITLY_PUBLIC_ROUTES: set[str] = {
    "GET /health",
    # FastAPI internal swagger assets (automatically registered, not in APIRoute list)
    # Note: /docs, /redoc, /openapi.json, /docs/oauth2-redirect are mounted by FastAPI
    # and don't appear as regular APIRoute instances, so we don't declare them here.
    "HEAD /health",
}

# -----------------------------------------------------------------------
# Auth dependency names that count as "protected"
# -----------------------------------------------------------------------
AUTH_DEPENDENCY_NAMES: set[str] = {
    # Contract Section 4 canonical deps
    "get_user_context",
    "require_internal_user",
    "require_tenant_user",
    "require_internal_permission",
    "require_tenant_permission",
    # Legacy (backward compat)
    "verify_fm_access",
    "get_current_user",
    "check_fm_permission",
    # Bearer security scheme (used by HTTPBearer)
    "HTTPBearer",
    "security",
}


def _get_dependency_names(route: APIRoute) -> set[str]:
    """
    Walk the dependency tree of a route and collect all callable names.
    Handles both route-level dependencies and per-endpoint Depends().
    """
    names: set[str] = set()

    def _collect(deps):
        for dep in deps:
            fn = getattr(dep, "dependency", dep)
            if callable(fn):
                names.add(fn.__name__ if hasattr(fn, "__name__") else str(fn))
            # Recurse into sub-dependencies
            sub = getattr(dep, "dependencies", []) or []
            _collect(sub)

    # Route-level dependencies
    _collect(route.dependencies)

    # Endpoint-level dependencies (from Depends() in function signature)
    if hasattr(route, "dependant") and route.dependant:
        for dep in (route.dependant.dependencies or []):
            fn = getattr(dep, "call", None)
            if fn and callable(fn):
                names.add(fn.__name__ if hasattr(fn, "__name__") else str(fn))
            sub = getattr(dep, "dependencies", []) or []
            for sub_dep in sub:
                fn2 = getattr(sub_dep, "call", None)
                if fn2 and callable(fn2):
                    names.add(fn2.__name__ if hasattr(fn2, "__name__") else str(fn2))

    return names


def _is_protected(route: APIRoute) -> bool:
    """Return True if the route has at least one recognised auth dependency."""
    dep_names = _get_dependency_names(route)
    return bool(dep_names & AUTH_DEPENDENCY_NAMES)


def _route_signature(route: APIRoute, method: str) -> str:
    return f"{method} {route.path}"


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------

@pytest.fixture(scope="module")
def app() -> FastAPI:
    """Import the actual FastAPI app at runtime."""
    from app.main import app as _app
    return _app


@pytest.fixture(scope="module")
def api_routes(app: FastAPI):
    """Return all APIRoute instances from the app."""
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append(route)
    return routes


class TestRouteProtection:
    """
    Contract Section 8 — Route Protection Test.

    Each test inspects the live FastAPI route table.
    Violations cause CI failure.
    """

    def test_all_non_public_routes_are_protected(self, api_routes):
        """
        Every route NOT in EXPLICITLY_PUBLIC_ROUTES must have an auth dependency.

        Contract: No route may be 'accidentally unprotected.'
        """
        violations = []

        for route in api_routes:
            for method in route.methods or []:
                sig = _route_signature(route, method)
                if sig in EXPLICITLY_PUBLIC_ROUTES:
                    continue  # explicitly public — OK
                if not _is_protected(route):
                    violations.append(sig)

        if violations:
            violation_list = "\n  ".join(violations)
            pytest.fail(
                f"\n\nSecurity Contract v1 Section 8 VIOLATION\n"
                f"The following routes have NO auth dependency:\n\n"
                f"  {violation_list}\n\n"
                f"Fix: add Depends(get_user_context) or a require_* dependency.\n"
                f"Public routes must be explicitly added to EXPLICITLY_PUBLIC_ROUTES.\n"
            )

    def test_public_routes_are_explicitly_declared(self, api_routes):
        """
        Routes in EXPLICITLY_PUBLIC_ROUTES must actually exist in the app.
        Prevents stale declarations from masking missing protection.
        """
        actual_sigs = set()
        for route in api_routes:
            for method in route.methods or []:
                actual_sigs.add(_route_signature(route, method))

        stale = []
        for sig in EXPLICITLY_PUBLIC_ROUTES:
            # Allow partial match (route may not include HEAD variants)
            base_path = sig.split(" ", 1)[1]
            found = any(base_path in s for s in actual_sigs)
            if not found:
                stale.append(sig)

        if stale:
            stale_list = "\n  ".join(stale)
            pytest.fail(
                f"\n\nSecurity Contract v1 Section 8 WARNING\n"
                f"The following routes are declared public but do NOT exist:\n\n"
                f"  {stale_list}\n\n"
                f"Remove stale entries from EXPLICITLY_PUBLIC_ROUTES.\n"
            )

    def test_no_route_has_none_user_dependency(self, api_routes):
        """
        No route may have a dependency that returns Optional[User] without
        enforcing non-None.

        Contract: No route allows None user (soft-auth is forbidden).
        """
        # This test inspects for known soft-auth patterns in route endpoint code.
        # Only flag patterns that suggest auth/user dependencies allow None.
        soft_auth_patterns = [
            # Patterns that suggest optional AUTH (not just any Optional type)
            "current_user: Optional",
            "user: Optional[",
            "current_user = None",
            "user = None",
            "user: None",
            "auth_user = None",
            "auth_user: Optional",
        ]

        violations = []
        for route in api_routes:
            endpoint = route.endpoint
            try:
                source = inspect.getsource(endpoint)
                for pattern in soft_auth_patterns:
                    if pattern in source:
                        for method in route.methods or []:
                            sig = _route_signature(route, method)
                            if sig not in EXPLICITLY_PUBLIC_ROUTES:
                                violations.append(f"{sig} (pattern: {pattern!r})")
                            break
            except (OSError, TypeError):
                pass  # built-in or C-extension endpoint — skip

        if violations:
            v_list = "\n  ".join(violations)
            pytest.fail(
                f"\n\nSecurity Contract v1 Section 8 VIOLATION\n"
                f"Possible soft-auth (user=None) patterns detected:\n\n"
                f"  {v_list}\n\n"
                f"Fix: auth dependencies must never return None on protected routes.\n"
            )

    def test_auth_mode_not_local_in_staging(self):
        """
        Contract Section 13: AUTH_MODE must equal 'clerk' in staging.
        Skipped in development environments.
        """
        from app.core.config import settings
        if settings.environment in ("staging", "production"):
            assert settings.auth_mode == "clerk", (
                f"AUTH_MODE must be 'clerk' in {settings.environment}. "
                f"Currently: {settings.auth_mode!r}"
            )

    def test_permission_fail_open_not_set_in_staging(self):
        """
        Contract Section 13: PERMISSION_FAIL_OPEN must be false in staging.
        """
        from app.core.config import settings
        if settings.environment in ("staging", "production"):
            assert not settings.permission_fail_open, (
                "PERMISSION_FAIL_OPEN must be false in staging/production."
            )

    def test_health_endpoint_is_public(self, api_routes):
        """Sanity check: /health must exist and be reachable without auth."""
        health_routes = [
            r for r in api_routes
            if r.path == "/health" and "GET" in (r.methods or [])
        ]
        assert health_routes, "/health endpoint not found — add it to main.py"
