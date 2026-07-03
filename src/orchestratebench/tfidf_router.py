"""Mid-strength routing baseline: TF-IDF cosine over the task *description*.

This sits between the two extremes compared in Experiment 1:

* ``FixedPolicy`` / ``HeuristicPolicy`` (``core.py``) route from surface
  metadata flags only -- they never read the description text.
* ``LLMPolicy`` (``routing_comparison.py``) reads the description with Claude.

``TfidfRouter`` reads the description but with no model and no learned
parameters: each route is represented by a fixed prototype string (its
``_DECISION_GUIDE`` definition plus a handful of intent cues), and a task is
routed to the highest cosine-similarity prototype under a plain TF-IDF vector
space. Crucially the prototypes are built from the *route definitions*, not the
gold labels, so there is no train/test leakage on the 26-case diagnostic.

Purpose (reviewer request A2): show that Exp 1 is not a two-point
keyword-vs-LLM extreme. A router that merely *reads the description* -- even a
shallow, LLM-free one -- already recovers the adversarial cases the flag
heuristic scores 0% on. That isolates the heuristic's blind spot as a property
of the surface-flag *mechanism*, not of case difficulty.

Pure-stdlib + NumPy; no scikit-learn dependency, so it runs anywhere the rest
of the harness runs and stays fully offline/reproducible.
"""

from __future__ import annotations

import math
import re
from typing import Dict, List

from .core import AgentTask, OrchestratorAction, RoutingDecision, SubAgentType

# Route prototypes: the route's own definition text + a few intent cues.
# These come from the *route semantics*, never from the gold-labelled cases.
_ROUTE_CUES: Dict[RoutingDecision, str] = {
    RoutingDecision.DIRECT_TOOL: (
        "a single lookup fetch retrieval that one tool answers directly "
        "look up pull find retrieve value document filing page balance invoice "
        "contract number name"
    ),
    RoutingDecision.CODE_EXECUTION: (
        "the task needs code written and run compute parse script chart "
        "calculate regex program execute deduplicate correlation extract"
    ),
    RoutingDecision.DECOMPOSE: (
        "a multi-step goal broken into ordered sub-tasks plan sequence "
        "coordinate audit map migrate stages onboard provision assign owners "
        "dependency"
    ),
    RoutingDecision.REASON_ONLY: (
        "the model answers from its own knowledge no tool or decomposition "
        "explain summarize why which reason define what stand for prime "
        "rephrase concise difference riskier"
    ),
}

_AGENT_FOR_DECISION: Dict[RoutingDecision, SubAgentType] = {
    RoutingDecision.DIRECT_TOOL: SubAgentType.TOOL_CALL,
    RoutingDecision.CODE_EXECUTION: SubAgentType.CODE,
    RoutingDecision.DECOMPOSE: SubAgentType.PLANNING,
    RoutingDecision.REASON_ONLY: SubAgentType.SUMMARIZATION,
}

_STOP = set(
    "the a an of to for in on and or is are be this that these those with by "
    "your you it its as at from into over per one two three most just what "
    "which why here their them then out up".split()
)


def _tokens(text: str) -> List[str]:
    return [w for w in re.findall(r"[a-z']+", text.lower()) if w not in _STOP and len(w) > 1]


class TfidfRouter:
    """Route a task to the highest cosine-similarity route prototype.

    The IDF weights are fit once over the route prototypes plus whatever task
    corpus is supplied at construction. Pass the full eval-set descriptions as
    ``corpus`` for a self-contained, deterministic vector space; the router
    holds no gold labels.
    """

    def __init__(self, corpus: List[str] | None = None) -> None:
        self._routes = list(_ROUTE_CUES.keys())
        proto_docs = [_tokens(_ROUTE_CUES[d]) for d in self._routes]
        extra_docs = [_tokens(t) for t in (corpus or [])]
        docs = proto_docs + extra_docs
        vocab = sorted({w for d in docs for w in d})
        self._vidx = {w: i for i, w in enumerate(vocab)}
        n = len(docs)
        df = [0] * len(vocab)
        for d in docs:
            for w in set(d):
                df[self._vidx[w]] += 1
        self._idf = [math.log((1 + n) / (1 + df[i])) + 1 for i in range(len(vocab))]
        self._protos = [self._vectorize(d) for d in proto_docs]

    def _vectorize(self, tokens: List[str]) -> List[float]:
        v = [0.0] * len(self._vidx)
        for w in tokens:
            i = self._vidx.get(w)
            if i is not None:
                v[i] += 1.0
        s = sum(v)
        if s:
            v = [x / s for x in v]
        v = [x * self._idf[i] for i, x in enumerate(v)]
        norm = math.sqrt(sum(x * x for x in v))
        return [x / norm for x in v] if norm else v

    @staticmethod
    def _cos(a: List[float], b: List[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def route(self, task: AgentTask) -> OrchestratorAction:
        tv = self._vectorize(_tokens(task.description))
        sims = [self._cos(tv, p) for p in self._protos]
        best = max(range(len(sims)), key=lambda i: sims[i])
        decision = self._routes[best]
        top = sims[best]
        agent = _AGENT_FOR_DECISION[decision]
        if decision == RoutingDecision.DIRECT_TOOL and task.requires_retrieval:
            agent = SubAgentType.RETRIEVAL
        return OrchestratorAction(
            task_id=task.task_id,
            decision=decision,
            selected_agent=agent,
            reasoning=f"TF-IDF description router: closest route prototype (cos={top:.2f}).",
            confidence=max(0.3, min(0.99, float(top))),
        )
