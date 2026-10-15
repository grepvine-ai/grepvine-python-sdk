from enum import StrEnum


class AddMemberRequestRole(StrEnum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    READER = "reader"

    def __str__(self) -> str:
        return str(self.value)
