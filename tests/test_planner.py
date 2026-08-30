from app.agent.planner import DeterministicPlanner, LLMPlanner


def test_deterministic_planner_selects_calculator():
    plan = DeterministicPlanner().plan("multiply 7 and 6")

    assert plan.tool_name == "calculator"
    assert plan.payload == {"a": 7, "b": 6, "operation": "multiply"}


def test_deterministic_planner_selects_weather():
    plan = DeterministicPlanner().plan("weather in Recife")

    assert plan.tool_name == "weather"
    assert plan.payload == {"location": "Recife"}


def test_llm_planner_parses_provider_response():
    planner = LLMPlanner(
        lambda _: '{"tool_name":"search","payload":{"query":"MCP"},"rationale":"lookup"}'
    )

    plan = planner.plan("find MCP")

    assert plan.tool_name == "search"
    assert plan.payload == {"query": "MCP"}
