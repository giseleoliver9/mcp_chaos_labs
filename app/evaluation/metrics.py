from collections import Counter
from statistics import mean
from typing import Any


def compute_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    successes = sum(1 for record in records if record["success"])
    recovered = sum(1 for record in records if record.get("recovered"))
    injected_failures = sum(1 for record in records if record.get("requested_failure") != "none")
    failures = total - successes
    safe_failures = sum(1 for record in records if record.get("safe_failure"))
    unsafe_responses = sum(1 for record in records if record.get("unsafe_response"))
    additional_tool_calls = sum(max(0, record.get("tool_calls", 1) - 1) for record in records)
    retries = [record.get("retries", 0) for record in records]
    latencies = [record.get("latency_ms", 0.0) for record in records]
    calls = [record.get("tool_calls", 1) for record in records]
    failure_types = Counter(record.get("failure_type", "none") for record in records)

    return {
        "executions": total,
        "successes": successes,
        "failures": failures,
        "success_rate": round(successes / total, 3) if total else 0.0,
        "recovery_rate": round(recovered / injected_failures, 3) if injected_failures else 0.0,
        "safe_failure_rate": round(safe_failures / failures, 3) if failures else 0.0,
        "unsafe_response_rate": round(unsafe_responses / total, 3) if total else 0.0,
        "recovery_efficiency": round(recovered / additional_tool_calls, 3) if additional_tool_calls else 0.0,
        "recovered_failures": recovered,
        "unrecovered_failures": sum(
            1 for record in records if not record["success"] and record.get("failure_type") != "none"
        ),
        "safe_failures": safe_failures,
        "unsafe_responses": unsafe_responses,
        "average_retries": round(mean(retries), 2) if retries else 0.0,
        "average_latency_ms": round(mean(latencies), 2) if latencies else 0.0,
        "average_tool_calls": round(mean(calls), 2) if calls else 0.0,
        "failure_types": dict(sorted(failure_types.items())),
    }
