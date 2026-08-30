from typing import Any


def search_tool(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload["query"]
    return {
        "status": "success",
        "result": f"Top simulated result for: {query}",
    }


def cached_search_tool(payload: dict[str, Any]) -> dict[str, Any]:
    query = payload["query"]
    return {
        "status": "success",
        "result": f"Cached fallback result for: {query}",
    }
