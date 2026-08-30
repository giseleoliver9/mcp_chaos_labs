import argparse
import json
from typing import Any

import uvicorn

from app.agent.baseline import BaselineAgent
from app.agent.planner import DeterministicPlanner
from app.agent.resilient import ResilientAgent
from app.chaos.failures import FailureType
from app.chaos.injector import ChaosInjector
from app.evaluation.runner import run_benchmark
from app.tools.registry import FALLBACK_TOOLS, TOOLS, list_tools

VERSION = "0.1.0"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcp-chaos-lab",
        description="Run agent reliability experiments against simulated MCP tool failures.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    subcommands = parser.add_subparsers(dest="command", required=True)

    benchmark = subcommands.add_parser("benchmark", help="Compare baseline and resilient agents.")
    benchmark.add_argument("--executions", type=int, default=100)
    benchmark.add_argument("--seed", type=int, default=7)
    benchmark.add_argument("--mode", choices=["deterministic", "seeded"], default="deterministic")
    benchmark.add_argument("--failure-probability", type=float, default=0.35)
    benchmark.add_argument("--output", default="results/benchmark.json")
    benchmark.add_argument("--trajectories", default="results/trajectories.jsonl")
    benchmark.set_defaults(handler=_benchmark)

    execute = subcommands.add_parser("execute", help="Run one tool call through an agent.")
    execute.add_argument("--agent", choices=["baseline", "advanced"], default="advanced")
    execute.add_argument("--tool", required=True, choices=list_tools())
    execute.add_argument(
        "--payload",
        required=True,
        help='JSON object or key=value pairs, e.g. "{\"a\":1,\"b\":2}" or "a=1,b=2".',
    )
    execute.add_argument("--failure", choices=[failure.value for failure in FailureType], default=FailureType.NONE.value)
    execute.set_defaults(handler=_execute)

    task = subcommands.add_parser("task", help="Plan and run a natural-language task.")
    task.add_argument("task")
    task.add_argument("--agent", choices=["baseline", "advanced"], default="advanced")
    task.add_argument("--planner", choices=["deterministic"], default="deterministic")
    task.add_argument("--failure", choices=[failure.value for failure in FailureType], default=FailureType.NONE.value)
    task.set_defaults(handler=_task)

    tools = subcommands.add_parser("tools", help="List available mock MCP tools.")
    tools.set_defaults(handler=_tools)

    serve = subcommands.add_parser("serve", help="Start the FastAPI server.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")
    serve.set_defaults(handler=_serve)

    return parser


def _benchmark(args: argparse.Namespace) -> int:
    result = run_benchmark(
        executions=args.executions,
        seed=args.seed,
        mode=args.mode,
        failure_probability=args.failure_probability,
        output_path=args.output,
        trajectory_path=args.trajectories,
    )
    _print_json(result)
    return 0


def _execute(args: argparse.Namespace) -> int:
    payload = _parse_payload(args.payload)
    failure = FailureType(args.failure)
    chaos = ChaosInjector(failure_rate=1.0)

    if args.agent == "baseline":
        result = BaselineAgent(TOOLS, chaos).execute(args.tool, payload, failure)
        _print_json({"agent": "baseline", "result": result})
        return 0

    result, attempts = ResilientAgent(TOOLS, FALLBACK_TOOLS, chaos).execute(args.tool, payload, failure)
    _print_json({"agent": "advanced", "result": result, "attempts": attempts})
    return 0


def _task(args: argparse.Namespace) -> int:
    planner = DeterministicPlanner()
    failure = FailureType(args.failure)
    chaos = ChaosInjector(failure_rate=1.0)

    if args.agent == "baseline":
        result = BaselineAgent(TOOLS, chaos).run_task(args.task, planner, failure)
        _print_json({"agent": "baseline", **result})
        return 0

    result = ResilientAgent(TOOLS, FALLBACK_TOOLS, chaos).run_task(args.task, planner, failure)
    _print_json({"agent": "advanced", **result})
    return 0


def _tools(_: argparse.Namespace) -> int:
    _print_json({"tools": list_tools()})
    return 0


def _serve(args: argparse.Namespace) -> int:
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def _parse_payload(raw_payload: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        payload = _parse_key_value_payload(raw_payload)
        if payload is None:
            raise SystemExit(f"Invalid payload: expected JSON object or key=value pairs. JSON error: {exc}") from exc

    if not isinstance(payload, dict):
        raise SystemExit("Payload must be a JSON object.")
    return payload


def _parse_key_value_payload(raw_payload: str) -> dict[str, Any] | None:
    if "=" not in raw_payload:
        return None

    payload: dict[str, Any] = {}
    for item in raw_payload.split(","):
        key, separator, value = item.partition("=")
        if not separator or not key.strip():
            return None
        payload[key.strip()] = _coerce_scalar(value.strip())
    return payload


def _coerce_scalar(value: str) -> Any:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    raise SystemExit(main())
