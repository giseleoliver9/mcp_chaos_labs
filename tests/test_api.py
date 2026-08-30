from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_execute_advanced_schema_mismatch():
    response = client.post(
        "/execute",
        json={
            "agent": "advanced",
            "tool_name": "calculator",
            "payload": {"a": 1, "b": 2},
            "failure": "schema_mismatch",
        },
    )

    assert response.status_code == 200
    assert response.json()["result"] == {"status": "success", "result": 3}


def test_task_endpoint_uses_planner():
    response = client.post(
        "/task",
        json={
            "agent": "advanced",
            "task": "weather in Recife",
            "failure": "schema_mismatch",
        },
    )

    assert response.status_code == 200
    assert response.json()["plan"]["tool_name"] == "weather"
