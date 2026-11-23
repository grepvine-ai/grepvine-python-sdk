from enum import StrEnum


class Permission(StrEnum):
    CREATE_INDEX = "create_index"
    MANAGE_AGENTS = "manage_agents"
    MANAGE_INDEX = "manage_index"
    MANAGE_MEMBERS = "manage_members"
    MANAGE_ORGANIZATION = "manage_organization"
    READ = "read"
    READ_USAGE = "read_usage"
    SEARCH = "search"
    WRITE = "write"

    def __str__(self) -> str:
        return str(self.value)
