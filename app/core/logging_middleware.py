"""Logging middleware for API request/response monitoring"""
import logging
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

logger = logging.getLogger(__name__)


class APILoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses for monitoring"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for health checks and static files
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        start_time = time.time()
        
        # Get request body (if any)
        request_body = None
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                request_body = await request.body()
                if request_body:
                    # Restore body for downstream handlers
                    await request._receive()
        except Exception as e:
            logger.warning(f"Could not read request body: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log request/response details
        log_data = {
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params) if request.query_params else None,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
            "client_ip": request.client.host if request.client else "unknown",
        }
        
        # Add request body for debugging (only for errors or debug mode)
        if request_body and (response.status_code >= 400 or logger.isEnabledFor(logging.DEBUG)):
            try:
                body_str = request_body.decode('utf-8')
                log_data["request_body"] = json.loads(body_str) if body_str else None
            except:
                log_data["request_body_raw"] = request_body[:500]  # First 500 bytes
        
        # Determine log level based on status code
        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400:
            log_level = logging.WARNING
        
        # Log with appropriate level
        logger.log(
            log_level,
            f"{request.method} {request.url.path} - {response.status_code} ({duration}ms)",
            extra=log_data
        )
        
        return response


def setup_logging():
    """Configure application logging"""
    from app.core.config import settings
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set specific logger levels
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    logger.info(f"Logging configured with level: {settings.log_level}")
