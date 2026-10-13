from enum import StrEnum


class UpdateMemberRequestRole(StrEnum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    READER = "reader"

    def __str__(self) -> str:
        return str(self.value)
