from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent.baseline import BaselineAgent
from app.agent.planner import DeterministicPlanner
from app.agent.resilient import ResilientAgent
from app.chaos.failures import FailureType
from app.chaos.injector import ChaosInjector
from app.evaluation.runner import run_benchmark
from app.tools.registry import FALLBACK_TOOLS, TOOLS, list_tools

app = FastAPI(
    title="MCP Chaos Lab",
    description="Benchmark baseline and resilient agents under simulated MCP tool failures.",
    version="0.1.0",
)


class ExecuteRequest(BaseModel):
    agent: str = Field(pattern="^(baseline|advanced)$")
    tool_name: str
    payload: dict[str, Any]
    failure: FailureType = FailureType.NONE


class TaskRequest(BaseModel):
    agent: str = Field(pattern="^(baseline|advanced)$")
    task: str
    failure: FailureType = FailureType.NONE


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tools")
def tools() -> dict[str, list[str]]:
    return {"tools": list_tools()}


@app.post("/execute")
def execute(request: ExecuteRequest) -> dict[str, Any]:
    if request.tool_name not in TOOLS:
        raise HTTPException(status_code=404, detail="Unknown tool")

    chaos = ChaosInjector(failure_rate=1.0)
    if request.agent == "baseline":
        result = BaselineAgent(TOOLS, chaos).execute(
            request.tool_name,
            request.payload,
            request.failure,
        )
        return {"agent": "baseline", "result": result}

    result, attempts = ResilientAgent(TOOLS, FALLBACK_TOOLS, chaos).execute(
        request.tool_name,
        request.payload,
        request.failure,
    )
    return {"agent": "advanced", "result": result, "attempts": attempts}


@app.post("/task")
def task(request: TaskRequest) -> dict[str, Any]:
    planner = DeterministicPlanner()
    chaos = ChaosInjector(failure_rate=1.0)

    if request.agent == "baseline":
        return {
            "agent": "baseline",
            **BaselineAgent(TOOLS, chaos).run_task(request.task, planner, request.failure),
        }

    return {
        "agent": "advanced",
        **ResilientAgent(TOOLS, FALLBACK_TOOLS, chaos).run_task(request.task, planner, request.failure),
    }


@app.post("/benchmark")
def benchmark(
    executions: int = 100,
    seed: int = 7,
    mode: str = "deterministic",
    failure_probability: float = 0.35,
) -> dict[str, Any]:
    return run_benchmark(
        executions=executions,
        seed=seed,
        mode=mode,
        failure_probability=failure_probability,
    )
