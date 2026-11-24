# Reproduction

## Local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
python run_benchmark.py
```

On macOS/Linux, activate the environment with:

```bash
source .venv/bin/activate
```

Benchmark output is written to:

- `results/benchmark.json`
- `results/trajectories.jsonl`

## CLI

Install the package locally:

```bash
pip install -e .[dev]
```

Run:

```bash
tool-failure-lab tools
tool-failure-lab benchmark
tool-failure-lab benchmark --mode seeded --executions 500 --failure-probability 0.35
tool-failure-lab execute --agent advanced --tool calculator --payload a=1,b=2 --failure schema_mismatch
tool-failure-lab task "weather in Recife" --agent advanced --failure schema_mismatch
```

## API

```bash
uvicorn app.main:app --reload
```

Run a benchmark:

```bash
curl -X POST "http://127.0.0.1:8000/benchmark?executions=100&seed=7"
```

Run a seeded chaos benchmark:

```bash
curl -X POST "http://127.0.0.1:8000/benchmark?mode=seeded&executions=500&seed=7&failure_probability=0.35"
```

Run a natural-language task through the planner:

```bash
curl -X POST http://127.0.0.1:8000/task ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"task\":\"weather in Recife\",\"failure\":\"schema_mismatch\"}"
```

Run one advanced agent execution with schema drift:

```bash
curl -X POST http://127.0.0.1:8000/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"tool_name\":\"calculator\",\"payload\":{\"a\":1,\"b\":2},\"failure\":\"schema_mismatch\"}"
```

## Docker

```bash
docker build -t tool-failure-lab .
docker run --rm -p 8000:8000 tool-failure-lab
```
