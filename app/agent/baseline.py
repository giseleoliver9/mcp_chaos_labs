from typing import Any

from app.chaos.failures import FailureType
from app.chaos.injector import ChaosInjector
from app.agent.planner import AgentPlanner
from app.tools.registry import ToolCallable


class BaselineAgent:
    """Direct tool runner: no retry, no fallback, no schema adaptation."""

    def __init__(
        self,
        tools: dict[str, ToolCallable],
        chaos: ChaosInjector | None = None,
    ) -> None:
        self.tools = tools
        self.chaos = chaos

    def execute(
        self,
        tool_name: str,
        payload: dict[str, Any],
        forced_failure: FailureType | None = None,
    ) -> dict[str, Any]:
        tool = self.tools[tool_name]
        if self.chaos:
            return self.chaos.execute(tool, payload, forced_failure)
        return tool(payload)

    def run_task(
        self,
        task: str,
        planner: AgentPlanner,
        forced_failure: FailureType | None = None,
    ) -> dict[str, Any]:
        plan = planner.plan(task)
        result = self.execute(plan.tool_name, plan.payload, forced_failure)
        return {"plan": plan.__dict__, "result": result}
