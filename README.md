# MCP Chaos Lab

MCP Chaos Lab is a small reliability benchmark for agents that depend on MCP-style tools.
Most demos show agents in perfect infrastructure conditions. This project shows what happens when the tool layer gets slow, unavailable, malformed, or silently changes schema.

The runtime architecture is a **Fault-Aware Agent Runtime**: an agent planning layer sits above explicit recovery policies at the tool boundary.

## What It Tests

The lab compares two agents:

- `BaselineAgent`: direct tool execution. If the tool fails, the task fails.
- `ResilientAgent`: validates output, classifies failures, retries transient timeouts, routes to fallbacks, adapts known schema drift, and aborts safely on malformed data.

Planning modes:

- `DeterministicPlanner`: reproducible task-to-tool planning for benchmarks.
- `LLMPlanner`: provider-neutral adapter for a real LLM planner. The caller injects the completion function, so the project does not force one vendor.

The reliability benchmark intentionally uses deterministic planning to isolate infrastructure behavior. A separate LLM-backed demo can demonstrate the same recovery layer with an actual reasoning agent.

Failure modes:

- `timeout`
- `tool unavailable`
- `malformed response`
- `schema mismatch`

Mock MCP-style tools:

- `calculator`
- `search`
- `weather`

## Latest Benchmark

Generated with:

```bash
python run_benchmark.py
```

100 executions, seed `7`:

| Agent | Task Success | Recovery Rate | Safe Failure | Unsafe Response | Recovery Efficiency | Avg Tool Calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 25.0% | 0.0% | 50.7% | 37.0% | 0.0 | 1.0 |
| Advanced | 75.0% | 66.7% | 100.0% | 0.0% | 1.0 | 1.5 |

Improvement: `+50.0 percentage points`.

The advanced agent still fails malformed responses intentionally. The point is not to hallucinate around bad data; it is to abort safely when recovery would be unsafe.

Seeded chaos benchmark, closer to production-style randomness:

```bash
mcp-chaos benchmark --mode seeded --executions 500 --failure-probability 0.35
```

Latest seeded run:

| Agent | Task Success | Recovery Rate | Safe Failure | Unsafe Response | Recovery Efficiency | Avg Tool Calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 63.4% | 0.0% | 44.8% | 20.2% | 0.0 | 1.0 |
| Advanced | 89.2% | 70.5% | 100.0% | 0.0% | 1.0 | 1.26 |

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_benchmark.py
pytest
```

## Install As A CLI

For local development:

```bash
pip install -e .[dev]
```

Then use the terminal command:

```bash
mcp-chaos-lab --version
mcp-chaos-lab tools
mcp-chaos-lab benchmark
mcp-chaos-lab benchmark --mode seeded --executions 500 --failure-probability 0.35
```

There is also a shorter alias:

```bash
mcp-chaos benchmark
```

Run one practical failure case:

```bash
mcp-chaos execute --agent advanced --tool search --payload query=order-12345 --failure unavailable
```

That command simulates a tool outage and shows the resilient agent routing the request to fallback instead of crashing.

Run a natural-language task through the planner:

```bash
mcp-chaos task "weather in Recife" --agent advanced --failure schema_mismatch
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open:

- `GET /health`
- `GET /tools`
- `POST /execute`
- `POST /task`
- `POST /benchmark`

Example tool execution:

```bash
curl -X POST http://127.0.0.1:8000/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"tool_name\":\"calculator\",\"payload\":{\"a\":1,\"b\":2},\"failure\":\"schema_mismatch\"}"
```

Example planned task:

```bash
curl -X POST http://127.0.0.1:8000/task ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"task\":\"weather in Recife\",\"failure\":\"schema_mismatch\"}"
```

## Architecture

```text
Task
  -> Agent Planner
  -> Tool Selection
  -> MCP Tool Layer
  -> Chaos Injector
       -> timeout
       -> malformed response
       -> tool unavailable
       -> schema mismatch
  -> Recovery Engine
       -> retry
       -> fallback
       -> schema refresh
       -> abort safely
  -> Tool Result
  -> Agent Final Response
  -> Trajectory Logger / Evaluator
```

## Why It Matters

Increasing agent autonomy did not improve reliability. Explicit recovery policies at tool boundaries did.

The most reliable behavior was not "try harder". It was knowing when to retry, when to switch tools, when to adapt, and when to stop.
