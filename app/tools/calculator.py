from typing import Any


def calculator_tool(payload: dict[str, Any]) -> dict[str, Any]:
    a = payload["a"]
    b = payload["b"]
    operation = payload.get("operation", "add")

    if operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        result = a / b
    else:
        result = a + b

    return {"status": "success", "result": result}
