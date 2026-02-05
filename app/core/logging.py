"""Logging configuration — uses loguru when available, else stdlib logging so tests run without loguru."""
import sys

try:
    from loguru import logger as _loguru
    _loguru.remove()
    _loguru.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        level="INFO",
        colorize=True,
    )
    try:
        from app.core.config import settings
        if settings.environment == "production":
            _loguru.add(
                "logs/fm_service_{time:YYYY-MM-DD}.log",
                rotation="00:00",
                retention="30 days",
                level=settings.log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            )
    except Exception:
        pass
    logger = _loguru
except ImportError:
    import logging
    logger = logging.getLogger("fm")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))
        logger.addHandler(h)
