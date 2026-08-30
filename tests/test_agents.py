import pytest

from app.agent.baseline import BaselineAgent
from app.agent.resilient import ResilientAgent
from app.chaos.failures import FailureType, SafeAbortError
from app.chaos.injector import ChaosInjector
from app.tools.registry import FALLBACK_TOOLS, TOOLS


def test_baseline_executes_tool_without_chaos():
    agent = BaselineAgent(TOOLS)

    result = agent.execute("calculator", {"a": 10, "b": 5})

    assert result == {"status": "success", "result": 15}


def test_baseline_dies_on_unavailable_tool():
    agent = BaselineAgent(TOOLS, ChaosInjector(failure_rate=1.0))

    with pytest.raises(ConnectionError):
        agent.execute("search", {"query": "mcp"}, FailureType.UNAVAILABLE)


def test_resilient_agent_recovers_timeout_with_retry():
    agent = ResilientAgent(TOOLS, FALLBACK_TOOLS, ChaosInjector(failure_rate=1.0))

    result, attempts = agent.execute("calculator", {"a": 2, "b": 3}, FailureType.TIMEOUT)

    assert result == {"status": "success", "result": 5}
    assert attempts[0]["strategy"] == "retry"
    assert attempts[-1]["recovered"] is True


def test_resilient_agent_recovers_unavailable_with_fallback():
    agent = ResilientAgent(TOOLS, FALLBACK_TOOLS, ChaosInjector(failure_rate=1.0))

    result, attempts = agent.execute("search", {"query": "mcp"}, FailureType.UNAVAILABLE)

    assert result["status"] == "success"
    assert "Cached fallback" in result["result"]
    assert attempts[-1]["strategy"] == "fallback"


def test_resilient_agent_adapts_schema_mismatch():
    agent = ResilientAgent(TOOLS, FALLBACK_TOOLS, ChaosInjector(failure_rate=1.0))

    result, attempts = agent.execute("calculator", {"a": 4, "b": 6}, FailureType.SCHEMA_MISMATCH)

    assert result == {"status": "success", "result": 10}
    assert attempts[-1]["strategy"] == "schema_refresh"


def test_resilient_agent_aborts_malformed_response():
    agent = ResilientAgent(TOOLS, FALLBACK_TOOLS, ChaosInjector(failure_rate=1.0))

    with pytest.raises(SafeAbortError):
        agent.execute("weather", {"location": "Sao Paulo"}, FailureType.MALFORMED)
