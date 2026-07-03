#!/usr/bin/env python
"""Experiment 1 baselines: Fixed / Heuristic(flags) / TF-IDF(description).

Adds a mid-strength routing baseline (reviewer request A2) so Exp 1 is not a
two-point keyword-vs-LLM extreme. Writes ``data/measured/exp1_baselines.csv``
with per-policy accuracy overall / aligned / adversarial on the 26-case
gold-labelled diagnostic. The LLM row (100% on this set) is measured
separately by ``reproduce_exp1.py`` and needs an API key; these three baselines
run fully offline.

Usage:
    python scripts/run_exp1_baselines.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from orchestratebench.core import FixedPolicy, HeuristicPolicy
from orchestratebench.routing_comparison import make_routing_eval_set
from orchestratebench.tfidf_router import TfidfRouter

OUT = Path("data/measured/exp1_baselines.csv")


def acc_by_kind(preds, cases):
    buckets = {"overall": [], "aligned": [], "adversarial": []}
    for (task, gold), pred in zip(cases, preds):
        ok = pred == gold
        buckets["overall"].append(ok)
        buckets[task.metadata["case"]].append(ok)
    return {k: (sum(v) / len(v) if v else float("nan")) for k, v in buckets.items()}


def main() -> None:
    cases = make_routing_eval_set()
    corpus = [t.description for t, _ in cases]
    policies = {
        "fixed": FixedPolicy(),
        "heuristic_flags": HeuristicPolicy(),
        "tfidf_description": TfidfRouter(corpus=corpus),
    }
    rows = []
    print(f"{'policy':20}{'overall':>9}{'aligned':>9}{'adversarial':>13}")
    for name, pol in policies.items():
        preds = [pol.route(t).decision for t, _ in cases]
        a = acc_by_kind(preds, cases)
        rows.append({"policy": name, **{k: round(v, 4) for k, v in a.items()}})
        print(f"{name:20}{a['overall']:9.3f}{a['aligned']:9.3f}{a['adversarial']:13.3f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["policy", "overall", "aligned", "adversarial"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
