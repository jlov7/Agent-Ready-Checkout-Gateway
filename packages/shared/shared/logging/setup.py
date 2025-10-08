from __future__ import annotations

import logging
import sys
from typing import Any

try:
    import structlog
except ImportError:  # pragma: no cover - optional dependency fallback
    structlog = None  # type: ignore


def configure_logging(level: str = "INFO") -> None:
    """Configure stdlib logging + structlog for JSON output."""

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level.upper())
    root_logger.addHandler(handler)

    if structlog is None:  # pragma: no cover - fallback path
        return

    timestamper = structlog.processors.TimeStamper(fmt="iso", default_timezone="UTC")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper(), 20)),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def bind_context(**kwargs: Any) -> None:
    """Bind context values to the current log context."""
    if structlog is None:  # pragma: no cover
        return
    structlog.contextvars.bind_contextvars(**kwargs)


def reset_context() -> None:
    """Reset bound logging context variables."""
    if structlog is None:  # pragma: no cover
        return
    structlog.contextvars.clear_contextvars()
