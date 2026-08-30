# Improvement Changelog

## V0 - Direct Tool Execution

Problem:
Any MCP/tool failure terminated the task.

Evidence:
Baseline succeeds only on clean executions in the seeded benchmark.

## V1 - Retry Policy

Problem:
Transient failures were treated the same as permanent failures.

Evidence:
Timeouts are recovered by retrying a fresh tool call.

## V2 - Failure Classification

Problem:
The agent could not choose a recovery strategy without knowing what failed.

Evidence:
Timeout, unavailable, malformed, and schema mismatch failures are classified separately.

## V3 - Fallback Routing

Problem:
Unavailable tools killed otherwise answerable tasks.

Evidence:
Search and weather requests can return cached fallback responses.

## V4 - Schema Validation

Problem:
Malformed output and schema drift looked identical without validation.

Evidence:
Known schema drift is adapted; malformed output aborts safely.

## V5 - Agent Planner Layer

Problem:
The first version benchmarked tool execution but did not model the agent planning step.

Evidence:
`DeterministicPlanner` now converts natural-language tasks into tool calls, while `LLMPlanner` provides a provider-neutral hook for real LLM planning.

## V6 - Safety Metrics

Problem:
Malformed responses counted only as failures, hiding that safe refusal is the desired behavior.

Evidence:
Metrics now include safe failure rate, unsafe response rate, and recovery efficiency.
