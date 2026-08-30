# Trajectories

Each benchmark execution writes JSON Lines to `results/trajectories.jsonl`.

Example record:

```json
{
  "timestamp": "2026-08-30T09:00:00.000000+00:00",
  "agent": "advanced",
  "tool": "calculator",
  "requested_failure": "schema_mismatch",
  "failure_type": "schema_mismatch",
  "success": true,
  "recovered": true,
  "safe_failure": false,
  "unsafe_response": false,
  "retries": 1,
  "tool_calls": 2,
  "latency_ms": 0.2,
  "attempts": [
    {
      "attempt": 1,
      "failure_type": "schema_mismatch",
      "strategy": "schema_refresh",
      "recovered": false
    },
    {
      "attempt": 2,
      "failure_type": "none",
      "strategy": "schema_refresh",
      "recovered": true
    }
  ]
}
```

This makes every success-rate claim auditable instead of just printed in a summary table.
