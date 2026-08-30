from enum import Enum


class FailureType(str, Enum):
    NONE = "none"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    MALFORMED = "malformed"
    SCHEMA_MISMATCH = "schema_mismatch"


class ToolUnavailableError(ConnectionError):
    """Raised when a tool cannot be reached."""


class ToolSchemaMismatchError(ValueError):
    """Raised when tool output cannot be adapted to the expected contract."""


class SafeAbortError(RuntimeError):
    """Raised when recovery refuses unsafe tool output."""

    def __init__(self, message: str, attempts: list[dict]) -> None:
        super().__init__(message)
        self.attempts = attempts


TRANSIENT_FAILURES = {FailureType.TIMEOUT}
