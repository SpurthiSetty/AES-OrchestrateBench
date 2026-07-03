from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_script(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_analyze_measured_wrapper_runs_without_editable_install() -> None:
    result = _run_script("scripts/analyze_measured.py", "--help")
    assert result.returncode == 0
    assert "Recompute measured" in result.stdout


def test_run_exp23_pipeline_wrapper_runs_without_editable_install() -> None:
    result = _run_script("scripts/run_exp23_pipeline.py", "--help")
    assert result.returncode == 0
    assert "Run Exp 2/3 end-to-end from one command" in result.stdout
