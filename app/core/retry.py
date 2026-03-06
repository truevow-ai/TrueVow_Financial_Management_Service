"""Retry utility for API calls with exponential backoff"""
import asyncio
import logging
from typing import TypeVar, Callable, Any, Optional
from functools import wraps
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_async(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
    logger_func: Optional[Callable[[str], None]] = None
):
    """Decorator for async function retry with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds between retries
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff calculation
        exceptions: Tuple of exception types to catch and retry
        logger_func: Optional logger function (defaults to logger.warning)
        
    Returns:
        Decorated async function with retry logic
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            log_func = logger_func or logger.warning
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries",
                            extra={"error": str(e)}
                        )
                        raise
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    jitter = asyncio.get_event_loop().time() % 100 / 100  # Add 0-0.99s jitter
                    total_delay = delay + jitter
                    
                    log_func(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {total_delay:.2f}s: {str(e)}"
                    )
                    
                    await asyncio.sleep(total_delay)
            
            # Should never reach here, but satisfy type checker
            raise last_exception
        
        return wrapper
    return decorator


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple = (Exception,),
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number with exponential backoff"""
        import random
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        jitter = random.uniform(0, 0.1 * delay)  # Add 10% jitter
        return delay + jitter


async def execute_with_retry(
    func: Callable[..., Any],
    *args: Any,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    **kwargs: Any
) -> T:
    """Execute async function with retry logic
    
    Args:
        func: Async function to execute
        *args: Positional arguments for func
        config: RetryConfig instance (uses defaults if None)
        on_retry: Optional callback called on each retry: fn(attempt, exception, delay)
        **kwargs: Keyword arguments for func
        
    Returns:
        Result from successful func execution
        
    Raises:
        Last exception if all retries fail
    """
    cfg = config or RetryConfig()
    last_exception = None
    
    for attempt in range(cfg.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except cfg.retryable_exceptions as e:
            last_exception = e
            
            if attempt == cfg.max_retries:
                logger.error(
                    f"{func.__name__} failed after {cfg.max_retries} retries",
                    extra={"error": str(e)}
                )
                raise
            
            delay = cfg.get_delay(attempt)
            
            logger.warning(
                f"{func.__name__} failed (attempt {attempt + 1}/{cfg.max_retries}), "
                f"retrying in {delay:.2f}s: {str(e)}"
            )
            
            if on_retry:
                on_retry(attempt + 1, e, delay)
            
            await asyncio.sleep(delay)
    
    # Should never reach here
    raise last_exception
