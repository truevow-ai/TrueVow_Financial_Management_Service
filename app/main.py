"""FastAPI application entry point"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.core.middleware import correlation_id_middleware, audit_context_middleware
from app.core.logging_middleware import APILoggingMiddleware, setup_logging
from app.core.service_registry import init_service_registry, shutdown_service_registry, register_fm_modules, register_fm_integrations
from app.api.v1 import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown"""
    # Setup logging configuration
    setup_logging()

    # ---------------------------------------------------------------
    # Security Contract v1 — Section 5: AUTH_MODE guard
    # ---------------------------------------------------------------
    # If ENV=production AND AUTH_MODE != "clerk" → hard crash.
    # No exception.  Local auth in production is FORBIDDEN.
    if settings.environment == "production" and settings.auth_mode != "clerk":
        raise RuntimeError(
            "AUTH_MODE=local is forbidden in production. "
            "Set AUTH_MODE=clerk and configure CLERK_JWKS_URL."
        )

    # Warn in non-production if PERMISSION_FAIL_OPEN is enabled
    if settings.permission_fail_open:
        if settings.environment == "production":
            raise RuntimeError(
                "PERMISSION_FAIL_OPEN=true is forbidden in production. "
                "Remove this flag before deployment."
            )
        logger.warning(
            "PERMISSION_FAIL_OPEN=true: DB permission failures will fall back to "
            "role-based defaults. This MUST be false in production."
        )

    # ---------------------------------------------------------------
    # Security Contract v1 — Section 4: Initialise JWKSManager
    # ---------------------------------------------------------------
    if settings.auth_mode == "clerk":
        if not settings.clerk_jwks_url:
            raise RuntimeError(
                "auth_mode=clerk requires CLERK_JWKS_URL to be set."
            )
        from app.auth.auth_context import init_jwks_manager
        init_jwks_manager(
            jwks_url=settings.clerk_jwks_url,
            cache_ttl=settings.clerk_jwks_cache_ttl,
        )
        logger.info(f"JWKSManager initialised for Clerk JWKS: {settings.clerk_jwks_url}")
    else:
        logger.info("auth_mode=local: using HS256 symmetric key (development only).")

    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Auth mode: {settings.auth_mode}")
    logger.info(f"Billing Service URL: {settings.billing_service_url or 'not configured'}")
    
    # ---------------------------------------------------------------
    # Service Registry — Register with Internal Ops (port 3006)
    # ---------------------------------------------------------------
    if settings.service_registry_enabled and settings.service_registry_url:
        try:
            await init_service_registry()
            logger.info(f"Service registry: registered as {settings.service_name}")
            
            # Register all FM modules built from day one
            await register_fm_modules()
            logger.info("Service registry: registered FM modules (GL, Treasury, AR, AP, Payroll, IC, Reporting)")
            
            # Register FM integrations with other services
            await register_fm_integrations()
            logger.info("Service registry: registered FM integrations (tenant_billing, cs_core, internal_ops, fm_frontend)")
            
        except Exception as e:
            # Fail fast if registry is required but unavailable
            if settings.environment == "production":
                logger.error(f"Service registry registration failed: {e}")
                raise
            else:
                logger.warning(f"Service registry registration failed (non-production, continuing): {e}")
    else:
        logger.info("Service registry: disabled or URL not configured")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")
    
    # Deregister from service registry
    await shutdown_service_registry()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="TrueVow Financial Management Service - Finance-grade accounting system",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Correlation ID middleware (first, so it tracks all requests)
app.middleware("http")(correlation_id_middleware)

# Audit context middleware: best-effort JWT → request.state.user_id/user_role
# Must run AFTER correlation_id_middleware so request.state.correlation_id is set.
# get_db_session() reads these three state attrs and injects them as
# SET LOCAL GUCs so fn_row_audit_log() trigger captures actor identity.
app.middleware("http")(audit_context_middleware)

# API request/response logging middleware
app.add_middleware(APILoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "fm-service",
        "version": settings.app_version,
    }
