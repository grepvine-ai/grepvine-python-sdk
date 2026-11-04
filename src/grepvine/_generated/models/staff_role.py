from enum import StrEnum


class StaffRole(StrEnum):
    ROOT = "root"
    SUPPORT = "support"

    def __str__(self) -> str:
        return str(self.value)
