import json

from app.evaluation.runner import run_benchmark


if __name__ == "__main__":
    result = run_benchmark()
    print(json.dumps(result, indent=2))
