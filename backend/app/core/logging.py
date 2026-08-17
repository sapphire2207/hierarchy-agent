"""Structured logging configuration."""

import logging
import sys

from backend.app.core.config import get_settings


def setup_logging(log_level: str | None = None) -> logging.Logger:
    """Configures application-wide structured logging format."""
    settings = get_settings()
    level_name = log_level or settings.log_level
    numeric_level = getattr(logging, level_name.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers.clear()
        root_logger.addHandler(handler)

    # Silence overly verbose third-party loggers if needed
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger("hierarchy_agent")
    logger.setLevel(numeric_level)
    return logger


logger = setup_logging()
