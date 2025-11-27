"""
Logging configuration for the trading bot.

Sets up rotating file handlers and console output with different formatting.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    logs_dir: str = "logs"
) -> logging.Logger:
    """
    Configure logging with rotating file handler and console output.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup log files to keep
        logs_dir: Directory to store log files

    Returns:
        Configured logger instance
    """
    Path(logs_dir).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    logger.handlers.clear()

    file_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        filename=os.path.join(logs_dir, "trading_bot.log"),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized with level: {log_level}")
    logger.info(f"Log files stored in: {os.path.abspath(logs_dir)}")

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (usually __name__ of the calling module)

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"trading_bot.{name}")
    return logging.getLogger("trading_bot")
