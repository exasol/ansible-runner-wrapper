## remove this functionality ?

import logging
from enum import Enum
from typing import Any

try:
    from rich import logging as rich_logging
except ImportError:  # pragma: no cover
    rich_logging = None  # type: ignore[assignment]

SUPPORTED_LOG_LEVELS = {
    "normal": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


class LogType(Enum):
    ANSIBLE = "ansible"


def get_status_logger(log_type: LogType) -> logging.Logger:
    return logging.getLogger(f"ai-lab-{log_type.value}")


def set_log_level(level: str):
    handler: logging.Handler
    handler_kwargs: dict[str, Any]
    if rich_logging is None:
        handler = logging.StreamHandler()
    else:
        handler_kwargs = {"rich_tracebacks": True}
        handler = rich_logging.RichHandler(**handler_kwargs)
    try:
        target_level = SUPPORTED_LOG_LEVELS[level]
        logging.basicConfig(
            level=target_level,
            datefmt="[%X]",
            format="%(name)s - %(message)s",
            handlers=[handler],
        )
        # For status logger we set at least level INFO, but allow also Debug if required by user
        for log_type in LogType:
            logger = get_status_logger(log_type)
            if target_level <= logging.INFO:
                logger.setLevel(target_level)
            else:
                logger.setLevel(logging.INFO)
    except KeyError as ex:
        raise ValueError(f"log level {level} is not supported!") from ex
