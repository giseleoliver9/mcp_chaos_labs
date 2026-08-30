from typing import Any

from pydantic import ValidationError

from app.agent.planner import AgentPlanner
from app.agent.recovery import adapt_schema, classify_failure, validate_response
from app.chaos.failures import FailureType, SafeAbortError, ToolUnavailableError
from app.chaos.injector import ChaosInjector
from app.tools.registry import ToolCallable


class ResilientAgent:
    def __init__(
        self,
        tools: dict[str, ToolCallable],
        fallback_tools: dict[str, ToolCallable],
        chaos: ChaosInjector,
        max_retries: int = 2,
    ) -> None:
        self.tools = tools
        self.fallback_tools = fallback_tools
        self.chaos = chaos
        self.max_retries = max_retries

    def execute(
        self,
        tool_name: str,
        payload: dict[str, Any],
        forced_failure: FailureType | None = None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        tool = self.tools[tool_name]
        attempts: list[dict[str, Any]] = []

        for attempt in range(1, self.max_retries + 2):
            try:
                # Forced chaos applies to the first attempt only; retries model a fresh call.
                failure = forced_failure if attempt == 1 else FailureType.NONE
                response = self.chaos.execute(tool, payload, failure)
                validated = validate_response(response)
                attempts.append(
                    {
                        "attempt": attempt,
                        "failure_type": FailureType.NONE.value,
                        "strategy": "direct",
                        "recovered": attempt > 1,
                    }
                )
                return validated, attempts
            except TimeoutError as exc:
                attempts.append(
                    {
                        "attempt": attempt,
                        "failure_type": classify_failure(exc, None).value,
                        "strategy": "retry",
                        "recovered": False,
                    }
                )
                if attempt > self.max_retries:
                    raise
            except ToolUnavailableError as exc:
                attempts.append(
                    {
                        "attempt": attempt,
                        "failure_type": classify_failure(exc, None).value,
                        "strategy": "fallback",
                        "recovered": False,
                    }
                )
                fallback = self.fallback_tools[tool_name]
                response = validate_response(fallback(payload))
                attempts.append(
                    {
                        "attempt": attempt + 1,
                        "failure_type": FailureType.NONE.value,
                        "strategy": "fallback",
                        "recovered": True,
                    }
                )
                return response, attempts
            except ValidationError as exc:
                failure_type = classify_failure(None, response)
                strategy = "schema_refresh" if failure_type == FailureType.SCHEMA_MISMATCH else "abort_safely"
                attempts.append(
                    {
                        "attempt": attempt,
                        "failure_type": failure_type.value,
                        "strategy": strategy,
                        "recovered": False,
                    }
                )
                if failure_type == FailureType.SCHEMA_MISMATCH:
                    adapted = validate_response(adapt_schema(response))
                    attempts.append(
                        {
                            "attempt": attempt + 1,
                            "failure_type": FailureType.NONE.value,
                            "strategy": "schema_refresh",
                            "recovered": True,
                        }
                    )
                    return adapted, attempts
                raise SafeAbortError("Malformed tool response", attempts) from exc

        raise RuntimeError("Recovery policy exhausted")

    def run_task(
        self,
        task: str,
        planner: AgentPlanner,
        forced_failure: FailureType | None = None,
    ) -> dict[str, Any]:
        plan = planner.plan(task)
        result, attempts = self.execute(plan.tool_name, plan.payload, forced_failure)
        return {"plan": plan.__dict__, "result": result, "attempts": attempts}
