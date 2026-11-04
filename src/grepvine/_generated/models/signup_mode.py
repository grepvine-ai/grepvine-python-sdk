from enum import StrEnum


class SignupMode(StrEnum):
    INVITE = "invite"
    OPEN = "open"

    def __str__(self) -> str:
        return str(self.value)
