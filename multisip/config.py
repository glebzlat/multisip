from dataclasses import dataclass

from .log_level import LogLevel


@dataclass
class Config:
    domain: str = "10.10.2.4"

    log_file_max_bytes: int = 5 * 1024 * 1024

    log_level = LogLevel.INFO
