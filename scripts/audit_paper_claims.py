#!/usr/bin/env python3
"""Standalone drift-check between the paper's headline numbers and the
committed measured CSVs under data/measured/.

This script intentionally does NOT import the orchestratebench package or its
statistics/analysis modules. It re-derives a handful of headline figures
directly from the raw CSVs with only the Python standard library, so it acts as
an *independent* cross-check against scripts/analyze_measured.py (which uses the
package's own analyzers). If both paths agree, that's a much stronger
reproducibility signal than either one alone -- and it cheaply catches the
"someone edited a CSV / the paper prose and forgot the other" drift that a
multi-editor workflow is prone to.

It runs no experiment and writes nothing; it only reads committed CSVs.

Usage:
    python3 scripts/audit_paper_claims.py
    python3 scripts/audit_paper_claims.py --strict   # exit 1 on any drift

Update CLAIMS below whenever the paper's headline numbers change.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "measured"

# Coarse sanity tolerance (not a statistical test).
TOLERANCE = 0.03

LATENT_MODES = {
    "ambiguous_delegation", "context_pollution", "conflicting_outputs", "premature_action",
}
TOOL_MODE = "tool_invocation_error"

# Expected values, sourced from paper/main.tex + PAPER.md (current measured state).
CLAIMS: dict[str, float] = {
    # Exp 2 arithmetic chain -- three-tier failure split (final-task success).
    "exp2.tool_invocation_error.mean_success": 1.00,
    "exp2.ambiguous_delegation.mean_success": 0.30,
    "exp2.context_pollution.mean_success": 0.00,
    "exp2.conflicting_outputs.mean_success": 0.00,
    "exp2.premature_action.mean_success": 0.00,
    # Exp 3 cascade radius by depth -- pooled latent modes (5-point curve).
    "exp3.depth3.latent_mean_cascade_radius": 0.93,
    "exp3.depth4.latent_mean_cascade_radius": 1.85,
    "exp3.depth5.latent_mean_cascade_radius": 2.80,
    "exp3.depth6.latent_mean_cascade_radius": 3.63,
    "exp3.depth7.latent_mean_cascade_radius": 4.67,
    "exp3.tool_invocation_error.mean_cascade_radius": 0.00,
    # Exp 4 decomposition fidelity.
    "exp4.monolithic.mean_delegation_fidelity": 0.37,
    "exp4.decompose.mean_delegation_fidelity": 1.00,
    # Cross-model invariance (Sonnet / Opus / Haiku) -- the tool-vs-latent
    # structure must hold across tiers: tool always recovers, the catastrophic
    # latent modes never do, regardless of model.
    "crossmodel.tool.min_success": 1.00,
    "crossmodel.tool.max_abs_delta": 0.00,
    "crossmodel.context_pollution.max_success": 0.00,
    "crossmodel.premature_action.max_success": 0.00,
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _bool(cell: str) -> float:
    return 1.0 if str(cell).strip().lower() in ("true", "1") else 0.0


def _exp2_claims() -> dict[str, float]:
    path = DATA_DIR / "exp2_real.csv"
    if not path.exists():
        return {}
    rows = _read_csv(path)
    out: dict[str, float] = {}
    for mode in (TOOL_MODE, *LATENT_MODES):
        vals = [_bool(r["final_task_success"]) for r in rows if r.get("failure_mode") == mode]
        if vals:
            out[f"exp2.{mode}.mean_success"] = mean(vals)
    return out


def _exp3_claims() -> dict[str, float]:
    path = DATA_DIR / "exp3_real.csv"
    if not path.exists():
        return {}
    rows = _read_csv(path)
    out: dict[str, float] = {}
    depths = sorted({int(r["depth"]) for r in rows})
    for depth in depths:
        vals = [
            float(r["cascade_radius"]) for r in rows
            if r.get("failure_mode") != TOOL_MODE and r.get("depth") == str(depth)
        ]
        if vals:
            out[f"exp3.depth{depth}.latent_mean_cascade_radius"] = mean(vals)
    tool = [float(r["cascade_radius"]) for r in rows if r.get("failure_mode") == TOOL_MODE]
    if tool:
        out["exp3.tool_invocation_error.mean_cascade_radius"] = mean(tool)
    return out


def _exp4_claims() -> dict[str, float]:
    path = DATA_DIR / "exp4_real.csv"
    if not path.exists():
        return {}
    rows = _read_csv(path)
    out: dict[str, float] = {}
    for policy in ("monolithic", "decompose"):
        vals = [float(r["delegation_fidelity"]) for r in rows if r.get("policy") == policy]
        if vals:
            out[f"exp4.{policy}.mean_delegation_fidelity"] = mean(vals)
    return out


def _crossmodel_claims() -> dict[str, float]:
    path = DATA_DIR / "exp2_crossmodel.csv"
    if not path.exists():
        return {}
    rows = {r["failure_mode"]: r for r in _read_csv(path)}
    out: dict[str, float] = {}
    success_cols = [c for c in (next(iter(rows.values())).keys() if rows else []) if c.startswith("success_")]
    if TOOL_MODE in rows and success_cols:
        tool = [float(rows[TOOL_MODE][c]) for c in success_cols]
        out["crossmodel.tool.min_success"] = min(tool)
        out["crossmodel.tool.max_abs_delta"] = float(rows[TOOL_MODE].get("max_abs_delta", max(tool) - min(tool)))
    for mode in ("context_pollution", "premature_action"):
        if mode in rows and success_cols:
            out[f"crossmodel.{mode}.max_success"] = max(float(rows[mode][c]) for c in success_cols)
    return out


def collect_observed() -> dict[str, float]:
    observed: dict[str, float] = {}
    observed.update(_exp2_claims())
    observed.update(_exp3_claims())
    observed.update(_exp4_claims())
    observed.update(_crossmodel_claims())
    return observed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true",
                        help="Exit with status 1 if any claim drifts beyond tolerance.")
    args = parser.parse_args(argv)

    if not DATA_DIR.exists():
        print(f"data/measured/ not found at {DATA_DIR}; nothing to audit.")
        return 0

    observed = collect_observed()
    drifted, missing = [], []

    print("Paper claim audit (independent of orchestratebench package)\n")
    print(f"{'claim':<48} {'paper':>8} {'observed':>10} {'status':>10}")
    print("-" * 80)
    for key, expected in CLAIMS.items():
        if key not in observed:
            missing.append(key)
            print(f"{key:<48} {expected:>8.3f} {'(no data)':>10} {'SKIPPED':>10}")
            continue
        actual = observed[key]
        status = "OK" if abs(actual - expected) <= TOLERANCE else "DRIFT"
        if status == "DRIFT":
            drifted.append((key, expected, actual))
        print(f"{key:<48} {expected:>8.3f} {actual:>10.3f} {status:>10}")

    print()
    if drifted:
        print(f"{len(drifted)} claim(s) drifted beyond tolerance ({TOLERANCE}):")
        for key, expected, actual in drifted:
            print(f"  - {key}: paper={expected:.3f} observed={actual:.3f} (delta={abs(actual-expected):.3f})")
            print("    -> update the paper, or this script's CLAIMS table, whichever is stale.")
    else:
        print("No drift detected for the claims this script checks.")
    if missing:
        print(f"\n{len(missing)} claim(s) could not be checked (missing CSV/columns): " + ", ".join(missing))

    return 1 if (args.strict and drifted) else 0


if __name__ == "__main__":
    raise SystemExit(main())
