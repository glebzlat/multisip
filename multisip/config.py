from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    domain: Optional[str] = None
