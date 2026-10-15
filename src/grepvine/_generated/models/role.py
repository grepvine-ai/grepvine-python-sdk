from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    OWNER = "owner"
    READER = "reader"

    def __str__(self) -> str:
        return str(self.value)
