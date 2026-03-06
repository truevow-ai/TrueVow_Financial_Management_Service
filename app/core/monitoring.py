"""
Monitoring and Observability Configuration for Financial Management Service

This module provides centralized logging, metrics, and monitoring configuration.
All API calls to external services (Billing Service, Treasury Service) are logged
with retry tracking and performance metrics.
"""
import logging
from typing import Dict, Any
from datetime import datetime


class MonitoringConfig:
    """Centralized monitoring configuration"""
    
    # Logging levels for different components
    LOG_LEVELS = {
        'default': logging.INFO,
        'api_requests': logging.INFO,
        'billing_integration': logging.INFO,
        'database_queries': logging.WARNING,
        'retry_events': logging.WARNING,
        'errors': logging.ERROR,
    }
    
    # Metrics to track
    METRICS_ENABLED = True
    
    # Retry configuration
    RETRY_CONFIG = {
        'max_retries': 3,
        'base_delay_seconds': 1.0,
        'max_delay_seconds': 30.0,
        'exponential_base': 2.0,
        'jitter_enabled': True,
    }
    
    # Performance thresholds
    PERFORMANCE_THRESHOLDS = {
        'api_response_time_warning_ms': 500,
        'api_response_time_critical_ms': 2000,
        'database_query_time_warning_ms': 100,
        'database_query_time_critical_ms': 1000,
        'billing_service_timeout_ms': 5000,
    }


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with standardized configuration.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level based on logger name
    if 'billing' in name.lower():
        logger.setLevel(MonitoringConfig.LOG_LEVELS['billing_integration'])
    elif 'retry' in name.lower():
        logger.setLevel(MonitoringConfig.LOG_LEVELS['retry_events'])
    elif 'database' in name.lower() or 'sqlalchemy' in name.lower():
        logger.setLevel(MonitoringConfig.LOG_LEVELS['database_queries'])
    else:
        logger.setLevel(MonitoringConfig.LOG_LEVELS['default'])
    
    return logger


def log_api_call(
    logger: logging.Logger,
    service: str,
    endpoint: str,
    method: str = "GET",
    status_code: int = None,
    duration_ms: float = None,
    success: bool = True,
    error_message: str = None,
    retry_attempt: int = None,
    metadata: Dict[str, Any] = None
):
    """
    Standardized logging for API calls to external services.
    
    Args:
        logger: Logger instance
        service: Service name (e.g., 'billing', 'treasury')
        endpoint: API endpoint path
        method: HTTP method
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        success: Whether the call succeeded
        error_message: Error message if failed
        retry_attempt: Current retry attempt number
        metadata: Additional context data
    """
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'service': service,
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'duration_ms': duration_ms,
        'success': success,
        'error_message': error_message,
        'retry_attempt': retry_attempt,
        **(metadata or {})
    }
    
    # Determine log level
    log_level = logging.INFO
    if not success:
        log_level = logging.ERROR if retry_attempt is None else logging.WARNING
    
    logger.log(log_level, f"{service.upper()} API Call: {method} {endpoint}", extra=log_data)


def log_retry_event(
    logger: logging.Logger,
    operation: str,
    attempt: int,
    max_attempts: int,
    delay_seconds: float,
    error: Exception
):
    """
    Log retry events with exponential backoff information.
    
    Args:
        logger: Logger instance
        operation: Operation being retried
        attempt: Current attempt number
        max_attempts: Maximum retry attempts
        delay_seconds: Delay before next retry
        error: Exception that triggered retry
    """
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'operation': operation,
        'attempt': attempt,
        'max_attempts': max_attempts,
        'delay_seconds': delay_seconds,
        'error_type': type(error).__name__,
        'error_message': str(error),
    }
    
    logger.warning(
        f"Retry {attempt}/{max_attempts} for {operation} after {delay_seconds}s",
        extra=log_data
    )


def log_performance_metric(
    logger: logging.Logger,
    metric_name: str,
    value: float,
    unit: str = "ms",
    threshold_warning: float = None,
    threshold_critical: float = None,
    metadata: Dict[str, Any] = None
):
    """
    Log performance metrics with threshold checking.
    
    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        threshold_warning: Warning threshold
        threshold_critical: Critical threshold
        metadata: Additional context
    """
    log_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'metric_name': metric_name,
        'value': value,
        'unit': unit,
        'threshold_warning': threshold_warning,
        'threshold_critical': threshold_critical,
        **(metadata or {})
    }
    
    # Check thresholds
    log_level = logging.INFO
    if threshold_critical and value >= threshold_critical:
        log_level = logging.CRITICAL
    elif threshold_warning and value >= threshold_warning:
        log_level = logging.WARNING
    
    logger.log(
        log_level,
        f"Performance Metric: {metric_name} = {value}{unit}",
        extra=log_data
    )


# Example usage in billing_adapter.py:
"""
logger = get_logger(__name__)

async def get_tenant_pricing(self, tenant_id: UUID) -> Optional[Dict]:
    start_time = time.time()
    try:
        async def _fetch():
            async with httpx.AsyncClient() as client:
                r = await client.get(...)
                r.raise_for_status()
                return r.json()
        
        result = await execute_with_retry(_fetch, config=BILLING_RETRY_CONFIG)
        
        # Log successful API call
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(
            logger=logger,
            service='billing',
            endpoint=f'/tenants/{tenant_id}/feature-access',
            status_code=200,
            duration_ms=duration_ms,
            success=True
        )
        
        # Check performance
        log_performance_metric(
            logger=logger,
            metric_name='billing_api_response_time',
            value=duration_ms,
            threshold_warning=500,
            threshold_critical=2000
        )
        
        return result
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        log_api_call(
            logger=logger,
            service='billing',
            endpoint=f'/tenants/{tenant_id}/feature-access',
            status_code=None,
            duration_ms=duration_ms,
            success=False,
            error_message=str(e)
        )
        raise
"""
