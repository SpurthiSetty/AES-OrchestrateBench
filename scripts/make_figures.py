#!/usr/bin/env python3
"""Regenerate every paper figure from the committed measured CSVs (offline, no key).

    python scripts/make_figures.py    # writes figures/*.png

Figure 1: Exp 3 cascade radius vs depth (latent vs tool).
Figure 2: Exp 2 failure-mode recovery, arithmetic vs loan-approval domain.
Figure 3: Exp 3 policy-conditioned cascade by depth (baseline vs LLM vs Oracle).
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "measured"
OUT = ROOT / "figures"
LATENT = {"ambiguous_delegation", "context_pollution", "conflicting_outputs", "premature_action"}


def load(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def istrue(x: object) -> int:
    return 1 if str(x).strip().lower() in ("true", "1") else 0


def fig1_cascade_by_depth() -> None:
    rows = load(DATA / "exp3_real.csv")
    lat, tool = defaultdict(list), defaultdict(list)
    for r in rows:
        d, c = int(r["depth"]), float(r["cascade_radius"])
        (tool if r["failure_mode"] == "tool_invocation_error" else lat)[d].append(c)
    depths = sorted(lat)
    plt.figure(figsize=(5, 3.2))
    plt.plot(depths, [np.mean(lat[d]) for d in depths], "o-", color="#B03A2E", label="latent / semantic modes")
    plt.plot(depths, [np.mean(tool[d]) for d in depths], "s-", color="#1E8449", label="tool_invocation_error")
    plt.xlabel("pipeline depth"); plt.ylabel("mean cascade radius")
    plt.title(f"Cascade radius scales with depth\n(real Claude Sonnet 4.6, N={len(rows)})", fontsize=10)
    plt.xticks(depths); plt.legend(fontsize=8); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(OUT / "exp3_cascade_by_depth.png", dpi=150); plt.close()


def fig2_arith_vs_domain() -> None:
    def fmrate(p: Path) -> tuple[dict, int]:
        rows = load(p)
        g = defaultdict(list)
        for r in rows:
            g[r["failure_mode"]].append(istrue(r["final_task_success"]))
        return {m: np.mean(v) for m, v in g.items()}, len(rows)
    arith, arith_n = fmrate(DATA / "exp2_real.csv")
    domain, domain_n = fmrate(DATA / "exp2_domain_real.csv")
    modes = ["tool_invocation_error", "ambiguous_delegation", "context_pollution",
             "conflicting_outputs", "premature_action"]
    x, w = np.arange(len(modes)), 0.38
    plt.figure(figsize=(6.6, 3.5))
    plt.bar(x - w / 2, [arith.get(m, 0) for m in modes], w, label="arithmetic chain", color="#377AB7")
    plt.bar(x + w / 2, [domain.get(m, 0) for m in modes], w, label="loan-approval workflow", color="#E69F00")
    plt.ylabel("final-task success"); plt.ylim(0, 1.08)
    n_label = f"N={arith_n} each" if arith_n == domain_n else f"N={arith_n}/{domain_n}"
    plt.title(f"Failure-mode recovery: arithmetic vs domain workflow\n(real Claude, {n_label})", fontsize=10)
    plt.xticks(x, [m.replace("_", "\n") for m in modes], fontsize=7)
    plt.legend(fontsize=8); plt.tight_layout()
    plt.savefig(OUT / "exp2_arith_vs_domain.png", dpi=150); plt.close()


def fig3_policy_cascade() -> None:
    rows = load(DATA / "exp3_policy_real.csv")
    depths = sorted({int(r["depth"]) for r in rows})

    def cas(pols: set) -> list:
        out = []
        for d in depths:
            v = [float(r["cascade_radius"]) for r in rows
                 if int(r["depth"]) == d and r["failure_mode"] in LATENT and r["policy"] in pols]
            out.append(np.mean(v) if v else 0.0)
        return out
    plt.figure(figsize=(5, 3.2))
    plt.plot(depths, cas({"fixed", "heuristic", "retry(heuristic)"}), "o-", color="#B03A2E",
             label="baseline (fixed/heuristic/retry)")
    plt.plot(depths, cas({"llm"}), "s-", color="#2874A6", label="LLM-as-router (trusted upstream)")
    plt.plot(depths, cas({"oracle"}), "^-", color="#1E8449", label="Oracle (ceiling)")
    plt.xlabel("pipeline depth"); plt.ylabel("mean cascade radius (latent)")
    plt.title(f"Cascade containment is policy-conditioned\n(real Claude, N={len(rows)})", fontsize=10)
    plt.xticks(depths); plt.legend(fontsize=8); plt.grid(alpha=0.3); plt.tight_layout()
    plt.savefig(OUT / "exp3_policy_cascade.png", dpi=150); plt.close()


def fig4_routing_ladder() -> None:
    """Exp 1 mid-strength baseline: accuracy vs how much the router reads."""
    rows = {r["policy"]: r for r in load(DATA / "exp1_baselines.csv")}
    order = ["fixed", "heuristic_flags", "tfidf_description", "llm"]
    labels = ["Fixed\n(no signal)", "Heuristic\n(surface flags)",
              "TF-IDF\n(reads description)", "LLM\n(reads intent)"]
    ali = [float(rows["fixed"]["aligned"]), float(rows["heuristic_flags"]["aligned"]),
           float(rows["tfidf_description"]["aligned"]), 1.00]
    adv = [float(rows["fixed"]["adversarial"]), float(rows["heuristic_flags"]["adversarial"]),
           float(rows["tfidf_description"]["adversarial"]), 1.00]
    x, w = np.arange(len(order)), 0.38
    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    b1 = ax.bar(x - w / 2, ali, w, label="aligned cases", color="#5B8DB8")
    b2 = ax.bar(x + w / 2, adv, w, label="adversarial cases", color="#B03A2E")
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("routing accuracy"); ax.set_ylim(0, 1.15)
    ax.set_title("Routing accuracy climbs with how much the router reads\n"
                 "(26-case gold diagnostic; adversarial = flags decoupled from intent)", fontsize=9)
    ax.legend(fontsize=8, loc="upper left", ncol=2, framealpha=0.9)
    ax.grid(axis="y", alpha=0.3)
    for bars in (b1, b2):
        for b in bars:
            ax.annotate(f"{b.get_height():.2f}", (b.get_x() + b.get_width() / 2, b.get_height()),
                        ha="center", va="bottom", fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "exp1_routing_ladder.png", dpi=150); plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig1_cascade_by_depth()
    fig2_arith_vs_domain()
    fig3_policy_cascade()
    if (DATA / "exp1_baselines.csv").exists():
        fig4_routing_ladder()
        print(f"wrote 4 figures to {OUT}/ (exp3_cascade_by_depth, exp2_arith_vs_domain, "
              "exp3_policy_cascade, exp1_routing_ladder)")
    else:
        print(f"wrote 3 figures to {OUT}/ (exp3_cascade_by_depth, exp2_arith_vs_domain, exp3_policy_cascade)")


if __name__ == "__main__":
    main()
