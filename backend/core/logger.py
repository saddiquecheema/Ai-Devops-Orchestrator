"""
=============================================================================
backend/core/logger.py — LOGGING SETUP
=============================================================================
USE:
  from backend.core.logger import get_logger
  logger = get_logger(__name__)
  logger.info("message")
=============================================================================
"""

import sys
from loguru import logger
from backend.core.config import settings


def setup_logging() -> None:
    """App startup pe ek baar call karo."""
    logger.remove()
    logger.add(
        sys.stdout,
        level    = settings.log_level,
        format   = (
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level:<8}</level> | "
            "<cyan>{name}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize = True,
    )


def get_logger(name: str):
    return logger.bind(name=name)
