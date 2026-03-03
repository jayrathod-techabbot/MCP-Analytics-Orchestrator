import logging
import sys
from logging.handlers import RotatingFileHandler

from backend.config import settings


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    has_stdout_handler = any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
        and getattr(handler, "stream", None) is sys.stdout
        for handler in logger.handlers
    )
    if not has_stdout_handler:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    settings.LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    target_log_path = str(settings.LOG_FILE_PATH.resolve())
    has_rotating_file_handler = any(
        isinstance(handler, RotatingFileHandler)
        and getattr(handler, "baseFilename", None) == target_log_path
        for handler in logger.handlers
    )
    if not has_rotating_file_handler:
        file_handler = RotatingFileHandler(
            filename=settings.LOG_FILE_PATH,
            maxBytes=settings.LOG_MAX_BYTES,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
