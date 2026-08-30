import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class TrajectoryLogger:
    def __init__(self, output_path: str | Path = "results/trajectories.jsonl") -> None:
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            **event,
        }
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
