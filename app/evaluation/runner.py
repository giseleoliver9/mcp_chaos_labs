import json
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.agent.baseline import BaselineAgent
from app.agent.recovery import classify_failure, validate_response
from app.agent.resilient import ResilientAgent
from app.chaos.failures import FailureType, SafeAbortError
from app.chaos.injector import ChaosInjector
from app.evaluation.metrics import compute_metrics
from app.tools.registry import FALLBACK_TOOLS, TOOLS
from app.trajectories.logger import TrajectoryLogger


@dataclass(frozen=True)
class TaskCase:
    tool_name: str
    payload: dict[str, Any]


TASKS = [
    TaskCase("calculator", {"a": 10, "b": 5, "operation": "add"}),
    TaskCase("calculator", {"a": 9, "b": 3, "operation": "multiply"}),
    TaskCase("search", {"query": "MCP reliability"}),
    TaskCase("weather", {"location": "Sao Paulo"}),
]


def build_failure_schedule(executions: int = 100) -> list[FailureType]:
    weights = [
        (FailureType.NONE, 0.25),
        (FailureType.TIMEOUT, 0.25),
        (FailureType.MALFORMED, 0.25),
        (FailureType.UNAVAILABLE, 0.13),
        (FailureType.SCHEMA_MISMATCH, 0.12),
    ]
    counts = [(failure, int(executions * weight)) for failure, weight in weights]
    remainder = executions - sum(count for _, count in counts)

    schedule: list[FailureType] = []
    for index, (failure, count) in enumerate(counts):
        schedule.extend([failure] * (count + (1 if index < remainder else 0)))
    return schedule


def build_seeded_failure_schedule(
    executions: int = 500,
    failure_probability: float = 0.35,
    rng: random.Random | None = None,
) -> list[FailureType]:
    rng = rng or random.Random()
    failure_modes = [
        FailureType.TIMEOUT,
        FailureType.MALFORMED,
        FailureType.UNAVAILABLE,
        FailureType.SCHEMA_MISMATCH,
    ]
    return [
        rng.choice(failure_modes) if rng.random() < failure_probability else FailureType.NONE
        for _ in range(executions)
    ]


def run_benchmark(
    executions: int = 100,
    seed: int = 7,
    mode: str = "deterministic",
    failure_probability: float = 0.35,
    output_path: str | Path = "results/benchmark.json",
    trajectory_path: str | Path = "results/trajectories.jsonl",
) -> dict[str, Any]:
    rng = random.Random(seed)
    chaos = ChaosInjector(failure_rate=1.0, rng=rng)
    baseline = BaselineAgent(TOOLS, chaos)
    resilient = ResilientAgent(TOOLS, FALLBACK_TOOLS, chaos)
    logger = TrajectoryLogger(trajectory_path)

    if mode == "deterministic":
        schedule = build_failure_schedule(executions)
        rng.shuffle(schedule)
    elif mode == "seeded":
        schedule = build_seeded_failure_schedule(executions, failure_probability, rng)
    else:
        raise ValueError("Benchmark mode must be deterministic or seeded")

    baseline_records = [
        _run_baseline_case(baseline, case, failure, logger)
        for case, failure in _iter_cases(schedule)
    ]
    resilient_records = [
        _run_resilient_case(resilient, case, failure, logger)
        for case, failure in _iter_cases(schedule)
    ]

    result = {
        "seed": seed,
        "mode": mode,
        "executions": executions,
        "failure_probability": failure_probability if mode == "seeded" else None,
        "schedule": {
            "normal": schedule.count(FailureType.NONE),
            "timeout": schedule.count(FailureType.TIMEOUT),
            "malformed": schedule.count(FailureType.MALFORMED),
            "unavailable": schedule.count(FailureType.UNAVAILABLE),
            "schema_mismatch": schedule.count(FailureType.SCHEMA_MISMATCH),
        },
        "baseline": compute_metrics(baseline_records),
        "advanced": compute_metrics(resilient_records),
    }
    result["improvement"] = {
        "success_rate_points": round(
            (result["advanced"]["success_rate"] - result["baseline"]["success_rate"]) * 100,
            1,
        )
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    return result


def _iter_cases(schedule: list[FailureType]):
    for index, failure in enumerate(schedule):
        yield TASKS[index % len(TASKS)], failure


def _run_baseline_case(
    agent: BaselineAgent,
    case: TaskCase,
    failure: FailureType,
    logger: TrajectoryLogger,
) -> dict[str, Any]:
    started = time.perf_counter()
    unsafe_response = False
    try:
        response = agent.execute(case.tool_name, case.payload, failure)
        validate_response(response)
        success = True
        observed_failure = FailureType.NONE
    except Exception as exc:
        success = False
        unsafe_response = "response" in locals()
        observed_failure = classify_failure(exc, locals().get("response"))

    record = {
        "agent": "baseline",
        "tool": case.tool_name,
        "requested_failure": failure.value,
        "failure_type": observed_failure.value,
        "success": success,
        "recovered": False,
        "safe_failure": not success and not unsafe_response,
        "unsafe_response": unsafe_response,
        "retries": 0,
        "tool_calls": 1,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
    }
    logger.log(record)
    return record


def _run_resilient_case(
    agent: ResilientAgent,
    case: TaskCase,
    failure: FailureType,
    logger: TrajectoryLogger,
) -> dict[str, Any]:
    started = time.perf_counter()
    attempts: list[dict[str, Any]] = []
    safe_failure = False
    try:
        _, attempts = agent.execute(case.tool_name, case.payload, failure)
        success = True
        observed_failure = failure if failure != FailureType.NONE else FailureType.NONE
    except Exception as exc:
        success = False
        observed_failure = failure if failure != FailureType.NONE else classify_failure(exc, locals().get("response"))
        if isinstance(exc, SafeAbortError):
            attempts = exc.attempts
        safe_failure = any(attempt.get("strategy") == "abort_safely" for attempt in attempts)

    record = {
        "agent": "advanced",
        "tool": case.tool_name,
        "requested_failure": failure.value,
        "failure_type": observed_failure.value,
        "success": success,
        "recovered": success and failure != FailureType.NONE,
        "safe_failure": safe_failure,
        "unsafe_response": False,
        "retries": max(0, len(attempts) - 1),
        "tool_calls": max(1, len(attempts)),
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "attempts": attempts,
    }
    logger.log(record)
    return record
