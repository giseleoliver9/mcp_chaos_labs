# MCP Chaos Lab

![Python 3.11+](docs/badges/python.svg) ![FastAPI](docs/badges/fastapi.svg) ![Pydantic](docs/badges/pydantic.svg) ![pytest](docs/badges/pytest.svg) ![Docker · opcional/optional](docs/badges/docker.svg)

[![Português (BR)](docs/badges/lang-pt-br.svg)](README.md) [![English](docs/badges/lang-en.svg)](README.en.md) [![Español](docs/badges/lang-es.svg)](README.es.md) [![Français](docs/badges/lang-fr.svg)](README.fr.md) [![简体中文](docs/badges/lang-zh-cn.svg)](README.zh-CN.md)

**What happens when a tool an AI agent depends on goes offline or returns broken data?**

MCP Chaos Lab is a Python simulator for answering that question. It sends the same request to two strategies, injects a failure, and shows which one returns a structurally valid response, uses a backup, or stops. You can try it without Docker, an API key, or a live model.

## MCP vs. this lab

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/docs/learn/architecture) is a standard that lets a compatible AI application discover and call tools exposed by a server. For example, a weather MCP server could expose a read-only tool called `get_rainfall(neighborhood, date)` that calls an existing weather API and returns the amount, station, source, and timestamp. The REST API can stay as it is; the MCP server is the adapter for AI clients.

**This lab does not implement an MCP server or client.** It simulates MCP-style tool calls inside Python to test how an agent handles failures. Its optional FastAPI endpoints are ordinary HTTP endpoints, not an MCP transport. The retry, fallback, and stop rules are implemented in the lab; MCP itself does not supply them.

## Demo: tool unavailable (30 seconds)

![Terminal demo: the baseline stops on a mock outage; the resilient policy returns a simulated fallback and stops on malformed data.](docs/mcp-chaos-lab-demo.gif)

The two strategies receive the same mock search request and the same forced outage. The baseline returns an error; the resilient strategy returns a simulated fallback and logs that it used it. The fallback is a mock fixture, not a live cache. The schema check validates response structure, not correctness or freshness. For the malformed response shown in the demo, the resilient strategy stops instead of passing invalid data onward.

Reproduce the three calls after installing the CLI (no API key, Docker, or live model required):

```bash
mcp-chaos execute --agent baseline --tool search --payload query=demo --failure unavailable
mcp-chaos execute --agent advanced --tool search --payload query=demo --failure unavailable
mcp-chaos execute --agent advanced --tool search --payload query=demo --failure malformed
```

## Run locally

**Requirements:** Python 3.11 or newer, and Git to clone. Without Git, choose **Code → Download ZIP** on GitHub, extract it, open the extracted folder, and start at `python -m venv .venv`.

### Windows (PowerShell)

```powershell
git clone https://github.com/giseleoliver9/mcp_chaos_labs.git
cd mcp_chaos_labs
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.cli execute --agent advanced --tool search --payload query=demo --failure unavailable
```

### macOS / Linux

```bash
git clone https://github.com/giseleoliver9/mcp_chaos_labs.git
cd mcp_chaos_labs
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m app.cli execute --agent advanced --tool search --payload query=demo --failure unavailable
```

The command prints `Cached fallback result for: demo` and `"recovered": true`. The response is simulated. Change `advanced` to `baseline` for the same outage without recovery (`ToolUnavailableError`), or use `advanced` with `--failure malformed` to see the deliberate stop (`SafeAbortError`). Both error cases are expected and exit with code 1.

Run `python -m app.cli benchmark` or `python -m pytest` with the same virtual-environment Python to reproduce the benchmark or run the tests.

## What It Tests

The small Python runtime compares two strategies:

- `BaselineAgent`: direct tool execution. If the tool fails, the task fails.
- `ResilientAgent`: validates output, classifies failures, retries transient timeouts, routes to fallbacks, adapts known schema drift, and aborts safely on malformed data.

Planning modes:

- `DeterministicPlanner`: reproducible task-to-tool planning.
- `LLMPlanner`: provider-neutral adapter for a real LLM planner. The caller injects the completion function, so the project does not force one vendor.

The reliability benchmark calls mock tools directly without a planner or live model, to isolate behavior at the tool boundary. The separate `task` command exercises the planning layer.

Failure modes:

- `timeout`
- `tool unavailable`
- `malformed response`
- `schema mismatch`

Mock MCP-style tools:

- `calculator`
- `search`
- `weather`

## Benchmark Results

Generated with:

```bash
python run_benchmark.py
```

100 matched simulated cases per strategy, seed `7`. Success means returning a response that passes structural validation:

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

With the same simulated tool calls, the strategy with explicit recovery policies returned more structurally valid responses. This benchmark does not measure agent autonomy or reliability in production.

The most reliable behavior was not "try harder". It was knowing when to retry, when to switch tools, when to adapt, and when to stop.
