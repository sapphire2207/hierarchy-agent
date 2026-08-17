"""Core configuration and logging utilities."""

from backend.app.core.config import get_settings, settings
from backend.app.core.logging import setup_logging

__all__ = ["get_settings", "settings", "setup_logging"]
