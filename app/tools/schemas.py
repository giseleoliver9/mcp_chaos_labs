from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    status: str
    result: Any
