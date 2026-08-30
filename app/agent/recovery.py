from typing import Any

from pydantic import ValidationError

from app.chaos.failures import FailureType, ToolUnavailableError
from app.tools.schemas import ToolResult


def classify_failure(error: Exception | None, response: dict[str, Any] | None) -> FailureType:
    if isinstance(error, TimeoutError):
        return FailureType.TIMEOUT
    if isinstance(error, ToolUnavailableError):
        return FailureType.UNAVAILABLE
    if response is None:
        return FailureType.NONE
    try:
        ToolResult.model_validate(response)
        return FailureType.NONE
    except ValidationError:
        if "data_v2" in response:
            return FailureType.SCHEMA_MISMATCH
        return FailureType.MALFORMED


def validate_response(response: dict[str, Any]) -> dict[str, Any]:
    return ToolResult.model_validate(response).model_dump()


def adapt_schema(response: dict[str, Any]) -> dict[str, Any]:
    if response.get("status_code") == 200 and "data_v2" in response:
        return {"status": "success", "result": response["data_v2"]}
    raise ValueError("Schema mismatch could not be adapted")
