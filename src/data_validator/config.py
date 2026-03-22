from enum import IntEnum


class ExitCode(IntEnum):
    """CLI exit codes: 0 = all checks passed, 1 = validation failure, 2 = runtime error."""

    PASS = 0
    FAIL = 1
    ERROR = 2
