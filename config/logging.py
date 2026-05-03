"""
Loguru asosidagi logging sozlamalari.
"""
import sys
import os
from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: str = "logs/bot.log") -> None:
    """Logging tizimini sozlash."""
    # Default handlerni o'chirish
    logger.remove()

    # Console output — rangli, chiroyli format
    logger.add(
        sys.stdout,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Fayl output — barcha loglar
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger.add(
        log_file,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        encoding="utf-8",
    )

    logger.info("📋 Logging tizimi ishga tushdi | Level: {}", log_level)
