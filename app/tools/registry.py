from collections.abc import Callable
from typing import Any

from app.tools.calculator import calculator_tool
from app.tools.search import cached_search_tool, search_tool
from app.tools.weather import cached_weather_tool, weather_tool

ToolCallable = Callable[[dict[str, Any]], dict[str, Any]]

TOOLS: dict[str, ToolCallable] = {
    "calculator": calculator_tool,
    "search": search_tool,
    "weather": weather_tool,
}

FALLBACK_TOOLS: dict[str, ToolCallable] = {
    "search": cached_search_tool,
    "weather": cached_weather_tool,
    "calculator": calculator_tool,
}


def get_tool(name: str) -> ToolCallable:
    return TOOLS[name]


def list_tools() -> list[str]:
    return sorted(TOOLS)
