from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


_LOGGING_CONFIGURED = False


def get_logger(name: str = "imalytix") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = True
    return logger


def _build_formatter() -> logging.Formatter:
    return logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")


def _build_rotating_file_handler(
    path: str,
    max_bytes: int,
    backup_count: int,
    formatter: logging.Formatter | None = None,
) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        filename=path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(formatter or _build_formatter())
    return handler


def setup_logging(settings: Any) -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    log_level = getattr(logging, str(getattr(settings, "log_level", "INFO")).upper(), logging.INFO)
    log_dir = Path(str(getattr(settings, "log_dir", "logs")))
    log_dir.mkdir(parents=True, exist_ok=True)
    app_log_path = Path(str(getattr(settings, "log_file", log_dir / "imalytix.log")))
    analysis_log_path = Path(str(getattr(settings, "analysis_log_file", log_dir / "analysis.log")))
    app_log_path.parent.mkdir(parents=True, exist_ok=True)
    analysis_log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_build_formatter())
    root_logger.addHandler(console_handler)

    root_logger.addHandler(
        _build_rotating_file_handler(
            str(app_log_path),
            int(getattr(settings, "log_max_bytes", 5 * 1024 * 1024)),
            int(getattr(settings, "log_backup_count", 5)),
        )
    )

    analysis_logger = logging.getLogger("imalytix.analysis")
    analysis_logger.handlers.clear()
    analysis_logger.setLevel(log_level)
    analysis_logger.propagate = False
    analysis_logger.addHandler(
        _build_rotating_file_handler(
            str(analysis_log_path),
            int(getattr(settings, "log_max_bytes", 5 * 1024 * 1024)),
            int(getattr(settings, "log_backup_count", 5)),
            logging.Formatter("%(message)s"),
        )
    )

    _LOGGING_CONFIGURED = True


def log_json(logger: logging.Logger, payload: dict[str, Any]) -> None:
    logger.info(json.dumps(payload, ensure_ascii=False, default=str))
