from enum import StrEnum


class QueryRequestMode(StrEnum):
    LITERAL = "literal"
    REGEX = "regex"

    def __str__(self) -> str:
        return str(self.value)
