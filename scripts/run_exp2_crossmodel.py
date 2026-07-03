#!/usr/bin/env python
"""Cross-model Experiment 2: run the five-failure-mode recovery probe on two
or more models and emit a side-by-side comparison (reviewer request C1).

Every measured claim in the paper currently rests on a single model
(claude-sonnet-4-6). This script re-runs the *same* arithmetic-chain harness
(`orbench-real-run --exp 2`) once per model into a model-tagged CSV, then pools
the per-failure-mode final-task-success rates into one table so the tier split
(tool fully recovered / ambiguous partial / latent never) can be checked for
model-invariance.

It is a thin, non-invasive wrapper: it does not touch the committed measured
CSV schema. Each model's run goes to `data/measured/exp2_<tag>.csv` via the
harness's existing `--out` flag, driven by the `ORCHESTRATEBENCH_LLM_MODEL`
env var the harness already honors.

Cost note: whole-project spend is ~$4; a second model on the five modes is a
few cents. Set ANTHROPIC_API_KEY to run for real; without it, pass --mock to
exercise the plumbing offline (deterministic mock agent, not real results).

Usage:
    # real, two models
    ANTHROPIC_API_KEY=... python scripts/run_exp2_crossmodel.py \
        --models claude-sonnet-4-6 claude-opus-4-1 --runs 30

    # offline smoke test of the pipeline
    python scripts/run_exp2_crossmodel.py --mock \
        --models claude-sonnet-4-6 claude-haiku-4 --runs 3
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "measured"
MODES = ["tool_invocation_error", "ambiguous_delegation", "context_pollution",
         "conflicting_outputs", "premature_action"]


def _tag(model: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")


def _istrue(x: object) -> int:
    return 1 if str(x).strip().lower() in ("true", "1") else 0


def run_one(model: str, runs: int, stages: int, mock: bool) -> Path:
    out = DATA / f"exp2_{_tag(model)}.csv"
    env = dict(os.environ, ORCHESTRATEBENCH_LLM_MODEL=model)
    if mock:
        env["ORCHESTRATEBENCH_MOCK"] = "1"
    cmd = [sys.executable, "-m", "orchestratebench.real_run",
           "--exp", "2", "--runs", str(runs), "--stages", str(stages),
           "--out", str(out)]
    print(f"\n=== {model}  ->  {out.name}  ({'MOCK' if mock else 'real'}) ===")
    subprocess.run(cmd, check=True, env=env, cwd=ROOT)
    return out


def rate_by_mode(path: Path) -> dict[str, float]:
    g = defaultdict(list)
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            g[r["failure_mode"]].append(_istrue(r["final_task_success"]))
    return {m: (sum(v) / len(v) if v else float("nan")) for m, v in g.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", nargs="+", default=["claude-sonnet-4-6", "claude-opus-4-1"],
                    help="Two or more model ids to compare.")
    ap.add_argument("--runs", type=int, default=30, help="Runs per failure mode.")
    ap.add_argument("--stages", type=int, default=4, help="Arithmetic chain length.")
    ap.add_argument("--mock", action="store_true",
                    help="Offline deterministic mock agent (pipeline test, not real results).")
    args = ap.parse_args()

    if not args.mock and not os.getenv("ANTHROPIC_API_KEY"):
        ap.error("no ANTHROPIC_API_KEY set. Provide a key, or pass --mock to test the pipeline.")

    rates = {m: rate_by_mode(run_one(m, args.runs, args.stages, args.mock)) for m in args.models}

    # pooled comparison table
    hdr = f"{'failure_mode':24}" + "".join(f"{m[-18:]:>20}" for m in args.models) + f"{'max|delta|':>12}"
    print("\n" + hdr)
    out_rows = []
    for mode in MODES:
        vals = [rates[m].get(mode, float("nan")) for m in args.models]
        finite = [v for v in vals if v == v]
        delta = (max(finite) - min(finite)) if len(finite) >= 2 else float("nan")
        print(f"{mode:24}" + "".join(f"{v:>20.3f}" for v in vals) + f"{delta:>12.3f}")
        out_rows.append({"failure_mode": mode,
                         **{f"success_{_tag(m)}": vals[i] for i, m in enumerate(args.models)},
                         "max_abs_delta": delta})

    out_csv = DATA / "exp2_crossmodel.csv"
    with out_csv.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader(); w.writerows(out_rows)
    print(f"\nwrote {out_csv}")
    print("Interpretation: small max|delta| on the tier ORDER (not absolute rates) => "
          "the three-tier split is model-invariant, strengthening C1.")


if __name__ == "__main__":
    main()
