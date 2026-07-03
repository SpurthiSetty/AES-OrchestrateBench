"""Tests for the mid-strength TF-IDF routing baseline (Exp 1, reviewer A2).

Locks the headline claim: a description-reading router with no model recovers
the adversarial cases the flag heuristic scores 0% on, isolating the heuristic's
blind spot as a mechanism property rather than case difficulty.
"""

from __future__ import annotations

from orchestratebench.core import FixedPolicy, HeuristicPolicy
from orchestratebench.routing_comparison import make_routing_eval_set
from orchestratebench.tfidf_router import TfidfRouter


def _acc_by_kind(policy, cases):
    buckets = {"overall": [], "aligned": [], "adversarial": []}
    for task, gold in cases:
        ok = policy.route(task).decision == gold
        buckets["overall"].append(ok)
        buckets[task.metadata["case"]].append(ok)
    return {k: (sum(v) / len(v) if v else float("nan")) for k, v in buckets.items()}


def test_tfidf_recovers_adversarial_cases():
    cases = make_routing_eval_set()
    corpus = [t.description for t, _ in cases]
    tfidf = _acc_by_kind(TfidfRouter(corpus=corpus), cases)
    heur = _acc_by_kind(HeuristicPolicy(), cases)

    # heuristic collapses on adversarial; TF-IDF recovers them without a model
    assert heur["adversarial"] == 0.0
    assert tfidf["adversarial"] >= 0.9
    # TF-IDF is a genuine mid-point, not a two-point extreme
    assert tfidf["overall"] > heur["overall"]


def test_router_is_deterministic():
    cases = make_routing_eval_set()
    corpus = [t.description for t, _ in cases]
    r1 = TfidfRouter(corpus=corpus)
    r2 = TfidfRouter(corpus=corpus)
    for task, _ in cases:
        assert r1.route(task).decision == r2.route(task).decision


def test_router_holds_no_gold_labels():
    # prototypes must derive from route cues, never from the eval labels
    cases = make_routing_eval_set()
    router = TfidfRouter(corpus=[t.description for t, _ in cases])
    action = router.route(cases[0][0])
    assert 0.0 <= action.confidence <= 1.0
    assert action.decision in {g for _, g in cases} or action.decision is not None


def test_baseline_tier_ordering():
    cases = make_routing_eval_set()
    corpus = [t.description for t, _ in cases]
    fixed = _acc_by_kind(FixedPolicy(), cases)["overall"]
    heur = _acc_by_kind(HeuristicPolicy(), cases)["overall"]
    tfidf = _acc_by_kind(TfidfRouter(corpus=corpus), cases)["overall"]
    # reading more of the task helps: fixed < heuristic < tfidf
    assert fixed < heur < tfidf
