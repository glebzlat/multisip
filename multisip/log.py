import logging
import logging.handlers

from pathlib import Path
from collections import deque

from PySide6.QtCore import QObject, Signal

from .config import Config


LOG_PREFIX = "app"


class LogBridge(QObject):

    lineAdded = Signal(str)


class TailQtHandler(logging.Handler):

    def __init__(self, bridge: LogBridge, max_lines: int = 500) -> None:
        super().__init__()
        self._bridge = bridge
        self._max_lines = max_lines
        self._lines: deque[tuple[str, int]] = deque(maxlen=self._max_lines)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = self.format(record)
            self._lines.append((line, record.levelno))
            self._bridge.lineAdded.emit(line)
        except Exception:
            self.handleError(record)

    def lines(self, level: int = logging.NOTSET) -> list[str]:
        return list(t[0] for t in self._lines if t[1] >= level)

    def text(self, level: int = logging.NOTSET) -> str:
        return "\n".join(t[0] for t in self._lines if t[1] >= level)

    def clear(self) -> None:
        self._lines.clear()

    @property
    def max_lines(self) -> int:
        return self._max_lines


def configure_logging(
    log_dir: Path,
    config: Config
) -> tuple[logging.Logger, LogBridge, TailQtHandler, logging.handlers.RotatingFileHandler]:
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOG_PREFIX)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="{asctime} [{levelname}] {name}: {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
        style="{"
    )

    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "multisip.log",
        maxBytes=config.log_file_max_bytes,
        backupCount=3,
        encoding="UTF-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    bridge = LogBridge()

    tail_handler = TailQtHandler(bridge)
    tail_handler.setLevel(logging.DEBUG)
    tail_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(tail_handler)

    return logger, bridge, tail_handler, file_handler


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"{LOG_PREFIX}.{name}")


def clear_log_file(logger: logging.Logger) -> None:
    for h in logger.handlers:
        if isinstance(h, logging.FileHandler):
            h.acquire()
            try:
                h.flush()
                h.stream.seek(0)
                h.stream.truncate()
            finally:
                h.release()
