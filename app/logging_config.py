"""Structured JSON logging configuration for production."""

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Formats log records as JSON with consistent fields for log aggregation.
    """

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if self.include_extra:
            extra_fields = {
                k: v
                for k, v in record.__dict__.items()
                if k
                not in (
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "stack_info",
                    "exc_info",
                    "exc_text",
                    "thread",
                    "threadName",
                    "message",
                    "taskName",
                    "asctime",
                )
            }
            if extra_fields:
                log_data["extra"] = extra_fields

        return json.dumps(log_data)


class ContextLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that includes context in every log message."""

    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging(log_level: str = "INFO") -> None:
    """Configure structured JSON logging.

    For production, all logs are JSON formatted for log aggregation systems.
    For development, use a human-readable format.
    """
    is_production = os.environ.get("ENVIRONMENT", "development") == "production"

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    if is_production:
        console_handler.setFormatter(JSONFormatter())
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)

    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str, **context) -> ContextLoggerAdapter:
    """Get a logger with optional context.

    Usage:
        logger = get_logger(__name__, user_id="123")
        logger.info("User did something")  # Logs {"user_id": "123", ...}
    """
    logger = logging.getLogger(name)
    return ContextLoggerAdapter(logger, context)
