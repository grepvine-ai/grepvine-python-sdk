from enum import StrEnum


class IndexState(StrEnum):
    CREATING = "creating"
    DELETE_FAILED = "delete_failed"
    DELETING = "deleting"
    READY = "ready"

    def __str__(self) -> str:
        return str(self.value)
