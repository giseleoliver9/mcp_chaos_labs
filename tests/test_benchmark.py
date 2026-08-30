from app.evaluation.runner import run_benchmark


def test_benchmark_produces_comparison(tmp_path):
    result = run_benchmark(
        executions=20,
        seed=42,
        output_path=tmp_path / "benchmark.json",
        trajectory_path=tmp_path / "trajectories.jsonl",
    )

    assert result["executions"] == 20
    assert result["baseline"]["success_rate"] < result["advanced"]["success_rate"]
    assert result["advanced"]["recovery_rate"] > result["baseline"]["recovery_rate"]
    assert result["advanced"]["unsafe_response_rate"] == 0.0
    assert result["advanced"]["recovery_efficiency"] > 0
    assert (tmp_path / "benchmark.json").exists()
    assert (tmp_path / "trajectories.jsonl").exists()


def test_seeded_benchmark_is_reproducible(tmp_path):
    first = run_benchmark(
        executions=50,
        seed=42,
        mode="seeded",
        failure_probability=0.35,
        output_path=tmp_path / "first.json",
        trajectory_path=tmp_path / "first.jsonl",
    )
    second = run_benchmark(
        executions=50,
        seed=42,
        mode="seeded",
        failure_probability=0.35,
        output_path=tmp_path / "second.json",
        trajectory_path=tmp_path / "second.jsonl",
    )

    assert first["schedule"] == second["schedule"]
    assert first["mode"] == "seeded"
