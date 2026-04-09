from __future__ import annotations

import logging

from enum import IntEnum
from typing import Optional


class LogLevel(IntEnum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG

    @staticmethod
    def names() -> list[str]:
        return list(n for n in dir(LogLevel) if str.isupper(n))

    @staticmethod
    def from_string(s: str) -> Optional[LogLevel]:
        for name in LogLevel.names():
            if s == name:
                return getattr(LogLevel, name)
        return None
