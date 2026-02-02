"""
Centralized logging for Astra.
- No global print override; use loggers in code.
- Rotating file handlers under ~/astra_logs or ASTRA_LOG_DIR.
- Console handler optional (enabled when not in test).
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(os.getenv("ASTRA_LOG_DIR", os.path.expanduser("~/astra_logs")))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB
LOG_BACKUP_COUNT = 5

LOG_FILES = {
    "general": LOG_DIR / "astra.log",
    "processing": LOG_DIR / "astra_processing.log",
    "discord": LOG_DIR / "astra_discord.log",
}


def setup_logging(
    level: str | int = "INFO",
    console: bool = True,
    test_mode: bool = False,
) -> None:
    """
    Configure root and Astra loggers. Call once at startup.
    In test_mode, only memory handler or minimal file logging can be used.
    """
    if test_mode:
        level = logging.DEBUG
        console = False

    root = logging.getLogger()
    root.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Remove existing handlers to avoid duplicates on re-run
    for h in root.handlers[:]:
        root.removeHandler(h)

    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        root.addHandler(ch)

    for name, path in LOG_FILES.items():
        try:
            fh = RotatingFileHandler(
                path, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT
            )
            fh.setFormatter(formatter)
            logger = logging.getLogger("astra." + name)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(fh)
            if not logger.propagate:
                logger.propagate = True
        except OSError as e:
            # e.g. permission or disk full
            logging.getLogger(__name__).warning("Could not create log file %s: %s", path, e)

    logging.getLogger("astra").info("Logging configured (dir=%s)", LOG_DIR)


def get_logger(name: str) -> logging.Logger:
    """Return a logger under the astra namespace."""
    if name.startswith("astra."):
        return logging.getLogger(name)
    return logging.getLogger("astra." + name)
