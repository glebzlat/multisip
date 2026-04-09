from dataclasses import dataclass
from typing import Optional

from .log_level import LogLevel


@dataclass
class Config:
    domain: Optional[str] = None

    log_file_max_bytes: int = 5 * 1024 * 1024

    log_level = LogLevel.WARNING
