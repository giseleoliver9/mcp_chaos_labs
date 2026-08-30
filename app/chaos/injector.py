import random
import time
from collections.abc import Callable, Sequence
from typing import Any

from app.chaos.failures import FailureType, ToolUnavailableError


class ChaosInjector:
    def __init__(
        self,
        failure_rate: float = 0.3,
        failure_modes: Sequence[FailureType] | None = None,
        timeout_seconds: float = 0.01,
        rng: random.Random | None = None,
    ) -> None:
        self.failure_rate = failure_rate
        self.failure_modes = tuple(
            failure_modes
            or (
                FailureType.TIMEOUT,
                FailureType.UNAVAILABLE,
                FailureType.MALFORMED,
                FailureType.SCHEMA_MISMATCH,
            )
        )
        self.timeout_seconds = timeout_seconds
        self.rng = rng or random.Random()

    def execute(
        self,
        tool: Callable[[dict[str, Any]], dict[str, Any]],
        payload: dict[str, Any],
        forced_failure: FailureType | None = None,
    ) -> dict[str, Any]:
        failure = forced_failure or self._pick_failure()

        if failure in (None, FailureType.NONE):
            return tool(payload)

        if failure == FailureType.TIMEOUT:
            time.sleep(self.timeout_seconds)
            raise TimeoutError("Tool execution timeout")

        if failure == FailureType.UNAVAILABLE:
            raise ToolUnavailableError("Tool unavailable")

        if failure == FailureType.MALFORMED:
            return {"invalid": "???"}

        if failure == FailureType.SCHEMA_MISMATCH:
            raw_result = tool(payload)
            return {
                "status_code": 200,
                "data_v2": raw_result.get("result"),
            }

        return tool(payload)

    def _pick_failure(self) -> FailureType | None:
        if self.rng.random() > self.failure_rate:
            return FailureType.NONE
        return self.rng.choice(self.failure_modes)
