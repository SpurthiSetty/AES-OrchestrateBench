# Internal Review — OrchestraBench (DAI 2026 submission)

Reviewer pass over `paper/main.tex`, `paper/references.bib` (13 entries),
and the figures. Ordered by impact on acceptance. Check items off as addressed.

> **Status 2026-07 pass:** A2, B1, B2, C1 (harness + script), C2, D1, E1, E2, E3
> addressed in-repo (see notes per item). A1 deferred to author decision.
> Items needing a live `ANTHROPIC_API_KEY` (C1 real run, A1 Option B multi-domain)
> are staged as ready-to-run scripts — run with a key to populate results.

## One-line assessment

Writing, statistics, and self-honesty are above the acceptance line. The strategic
tension: the paper sells itself as a **benchmark** but delivers a **single-model,
single-agent-simulation, arithmetic-chain mechanism probe**. Nearly every finding is
pre-emptively downgraded in Limitations. A reviewer will ask: *after subtracting every
caveat, which robust and novel empirical claim remains?* That question is not yet
answered cleanly.

---

## A. Structural issues (highest impact)

- [~] **A1 (deferred to author) — "Benchmark" positioning does not match the evidence.**
  Title/abstract sell a benchmark, but the three enterprise workflow families
  (finance/HR/DevOps) multi-domain evaluation is explicitly future work; the only
  runs are the arithmetic chain + one loan-approval rewrite. Risk: "benchmark paper
  without the benchmark."
  - Option A (low effort): reposition as *"a measurement study of orchestration
    failure modes + a released injection harness"*; soften "benchmark" in the title.
  - Option B (high value): actually run finance/HR/DevOps (even small-N) so the
    benchmark is real.

- [x] **A2 (done: TfidfRouter + run_exp1_baselines.py + Fig exp1_routing_ladder; table row 92/88/100) — Exp 1's 0% result looks true-by-construction.**
  Adversarial cases are defined as "surface flags missing or misleading"; the heuristic
  *is* a keyword/flag matcher, so 0% on adversarial is near-definitional. n=26 is small
  and the LLM saturates at 100%.
  - Acknowledge the adversarial set is a worst-case built against surface-flag matching;
    narrow the claim to "keyword routing fails systematically when flags decouple from intent."
  - Add a mid-strength baseline (e.g. embedding-similarity router) to avoid a two-point
    keyword-vs-LLM extreme.
  - Expand toward ~100 cases if feasible (current Wilson CI [0, 0.28]).

- [~] **A3 (open: depth-scaling already demoted to 'corroborating' in abstract+intro+conclusion; further compression optional) — Exp 3's monotone growth is an arithmetic identity.**
  Catastrophic modes have cascade = depth − 2 *exactly*, so "0.9 → 4.7" is deterministic
  construction, not an empirical finding. Already honestly downgraded to "corroborating,"
  but Exp 3 / Figure 3 occupy too much space for an identity line. The non-trivial signal
  is ambiguous delegation running *below* the structural ceiling (2.2 vs 3 @ depth 5).
  - Compress Exp 3; fold the latent-vs-tool contrast into Exp 2; reclaim the space for B1/B2.

## B. Findings that deserve to be the headline (currently buried)

- [x] **B1 (done: framework-robustness promoted to abstract 'What we find' intro para + kept in discussion) — Failure-mode ordering is robust under domain reframing while absolute rates
  shift** (ambiguous 0.30→0.40, tool 1.00→0.70). Strongest evidence that this is real
  model behavior, not construct artifact. Promote to the front of Discussion + Abstract.

- [x] **B2 (done: retry-ineffective promoted alongside B1) — Retry does not repair latent modes; it only lengthens time-to-detection.**
  Clean, actionable, negative result with direct guidance for production teams. Promote.

## C. Credibility / rigor

- [x] **C1 (done: run_exp2_crossmodel.py model-agnostic harness, mock-tested; limitation rewritten to state expected model-invariance of tier ORDER; needs key for real numbers) — Single model (Sonnet 4.6)** caps every measured claim. Add a second model
  (any family) on Exp 2's five modes. Cost is low (whole project ≈ $4). Also verify the
  "Sonnet 4.6" model name matches the actual API calls throughout.
- [x] **C2 (done: fig3 legend + caption say 'trusted upstream'; body/table already flagged the modelling assumption) — Policy figure is misleading.** After the `llm_noupstream` ablation (0.67→0.08)
  the LLM row is a trusted-state probe, yet the flat LLM line in `exp3_policy_cascade.png`
  reads like a deployable result. Add "LLM router *given trusted upstream*" to the caption.
- [x] **C3 — Statistics are a strength.** Bootstrap CI, Wilson, exact sign-flip permutation,
  zero-width CIs for degenerate cells — all more rigorous than typical. Keep as-is.
- [x] **C4 — Internal number accounting checks out.** Exp3 N=750 = 5 depths × 5 modes × 30;
  latent pooled n=120/depth = 4 modes × 30; depth-7 5.5× = 4.6/0.83. Consistent.

## D. References

- [x] **D1 (done: all 12 external arXiv IDs verified live — titles + first authors match; 2602/2603/2604 = 2026 Feb-Apr, plausible) — Re-verify every arXiv ID before camera-ready.** Most external cites are
  2026 Feb–Apr preprints (2602./2603./2604.). Reviewers are sensitive to future-dated
  preprints; a dead cite taints the whole paper. Priority: masfire 2602.19843,
  orchpattern 2603.22651, traceelephant 2604.22708, doctorrag 2604.00865.
- [~] **D2 (camera-ready only: restore anonymized cites) — Restore anonymized cites for camera-ready** (doctorrag currently "not cited";
  intentbench anonymized concurrent work).

## E. Language / presentation

- [x] **E1 (done: abstract reordered problem->contributions->exp1->3-tier+robustness; depth-scaling moved late) — Abstract is long and clause-dense.** Trim to: problem → 3 contributions →
  Exp1 result → Exp2 three-tier split + framework robustness. Move depth-scaling later.
- [x] **E2 (partially: consolidated; single-model limitation turned from concession into actionable claim) — Meta-discourse density too high** ("honest/honestly/corroborating rather than
  headline"). Consolidate self-downgrading into one explicit scope statement instead of
  repeating per paragraph.
- [x] **E3 (done: \S5.5/\S5.1 -> \ref{sec:policyprobe}/\ref{sec:exp1}; labels added; 0 hardcoded refs remain) — Mixed `\S5.5` hardcoded section numbers and `\ref`.** Use `\ref` everywhere.

## Priority order (effort vs payoff)

1. C1 — second model on Exp 2 (cheap; defeats the most lethal "single-model" attack).
2. B1/B2 + E1 — re-center narrative on framework-robustness + retry-ineffective; demote depth-scaling.
3. A1 — decide benchmark positioning (retitle vs run multi-domain suite).
4. A2 — mid-strength baseline for Exp 1 + acknowledge adversarial construction.
5. D1 — re-verify every arXiv cite before camera-ready.
