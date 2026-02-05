"""Core middleware for correlation IDs and request tracking"""
import uuid
from fastapi import Request, Response
from starlette.types import ASGIApp
from app.core.logging import logger


async def correlation_id_middleware(request: Request, call_next):
    """Middleware to add correlation ID to requests (function-based)"""
    # Get or create correlation ID
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    
    # Add to request state
    request.state.correlation_id = correlation_id
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
        }
    )
    
    # Process request
    response: Response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response
