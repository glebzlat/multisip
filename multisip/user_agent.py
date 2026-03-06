from dataclasses import dataclass, field
from enum import StrEnum


def user_agent_password_from_user(user: int) -> str:
    return f"{user}{user}"


class Status(StrEnum):
    PENDING = "zzz"
    REGISTERED = "OK"
    UNREGISTERED = "ERR"


@dataclass(frozen=True)
class UserAgent:
    user: int
    domain: str
    password: str = field(default="", repr=False, hash=False)
