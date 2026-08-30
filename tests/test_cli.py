from app.cli import main


def test_cli_lists_tools(capsys):
    exit_code = main(["tools"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "calculator" in captured.out


def test_cli_executes_advanced_schema_mismatch(capsys):
    exit_code = main(
        [
            "execute",
            "--agent",
            "advanced",
            "--tool",
            "calculator",
            "--payload",
            '{"a":1,"b":2}',
            "--failure",
            "schema_mismatch",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"result": 3' in captured.out


def test_cli_accepts_key_value_payload(capsys):
    exit_code = main(
        [
            "execute",
            "--agent",
            "advanced",
            "--tool",
            "search",
            "--payload",
            "query=order-12345",
            "--failure",
            "unavailable",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Cached fallback result for: order-12345" in captured.out


def test_cli_runs_task_through_planner(capsys):
    exit_code = main(
        [
            "task",
            "weather in Recife",
            "--agent",
            "advanced",
            "--failure",
            "schema_mismatch",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"tool_name": "weather"' in captured.out
    assert '"schema_refresh"' in captured.out


def test_cli_benchmark_writes_output(tmp_path, capsys):
    exit_code = main(
        [
            "benchmark",
            "--executions",
            "20",
            "--output",
            str(tmp_path / "benchmark.json"),
            "--trajectories",
            str(tmp_path / "trajectories.jsonl"),
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "benchmark.json").exists()
    assert (tmp_path / "trajectories.jsonl").exists()
    assert "improvement" in capsys.readouterr().out


def test_cli_seeded_benchmark(tmp_path, capsys):
    exit_code = main(
        [
            "benchmark",
            "--mode",
            "seeded",
            "--executions",
            "50",
            "--failure-probability",
            "0.35",
            "--output",
            str(tmp_path / "benchmark.json"),
            "--trajectories",
            str(tmp_path / "trajectories.jsonl"),
        ]
    )

    assert exit_code == 0
    assert '"mode": "seeded"' in capsys.readouterr().out
