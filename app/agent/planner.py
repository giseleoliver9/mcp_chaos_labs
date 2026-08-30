import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolPlan:
    tool_name: str
    payload: dict[str, Any]
    rationale: str


class AgentPlanner(Protocol):
    def plan(self, task: str) -> ToolPlan:
        """Convert a user task into a tool call plan."""


class DeterministicPlanner:
    """Rule-based planner used by benchmarks to isolate infrastructure behavior."""

    def plan(self, task: str) -> ToolPlan:
        normalized = task.lower()

        if any(word in normalized for word in ("weather", "forecast", "temperature", "clima", "tempo")):
            location = _extract_after(task, ("in", "for", "em", "de")) or "Sao Paulo"
            return ToolPlan("weather", {"location": location}, "Task asks for weather information.")

        if any(word in normalized for word in ("search", "find", "lookup", "pesquise", "procure", "busque")):
            query = _strip_command_words(task)
            return ToolPlan("search", {"query": query}, "Task asks for information lookup.")

        numbers = [int(value) for value in re.findall(r"-?\d+", task)]
        if len(numbers) >= 2:
            operation = "add"
            if any(word in normalized for word in ("multiply", "times", "produto", "multiplique")):
                operation = "multiply"
            elif any(word in normalized for word in ("subtract", "minus", "subtraia", "menos")):
                operation = "subtract"
            elif any(word in normalized for word in ("divide", "divida")):
                operation = "divide"
            return ToolPlan(
                "calculator",
                {"a": numbers[0], "b": numbers[1], "operation": operation},
                "Task contains numeric calculation intent.",
            )

        return ToolPlan("search", {"query": task}, "Defaulting to search for open-ended task.")


class LLMPlanner:
    """Provider-neutral LLM planner.

    The caller injects a completion function so the project stays portable. The function
    receives a prompt string and must return JSON with tool_name, payload, and rationale.
    """

    def __init__(self, complete: Callable[[str], str]) -> None:
        self.complete = complete

    def plan(self, task: str) -> ToolPlan:
        raw = self.complete(_planner_prompt(task))
        data = json.loads(raw)
        return ToolPlan(
            tool_name=data["tool_name"],
            payload=data["payload"],
            rationale=data.get("rationale", "LLM selected the tool."),
        )


def _planner_prompt(task: str) -> str:
    return (
        "Choose one tool for this task. Available tools: calculator, search, weather.\n"
        "Return only JSON with keys: tool_name, payload, rationale.\n"
        f"Task: {task}"
    )


def _extract_after(text: str, markers: tuple[str, ...]) -> str | None:
    pattern = r"\b(" + "|".join(re.escape(marker) for marker in markers) + r")\s+(.+)$"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(2).strip(" ?.") if match else None


def _strip_command_words(task: str) -> str:
    cleaned = re.sub(r"\b(search|find|lookup|pesquise|procure|busque)\b", "", task, flags=re.IGNORECASE)
    return cleaned.strip(" :?.") or task
