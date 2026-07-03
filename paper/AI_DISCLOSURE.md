# Generative AI Usage Disclosure — OrchestraBench (DAI 2026)

> Draft for the **OpenReview submission form's AI-disclosure field** — NOT part of
> the anonymized PDF. DAI 2026 requires disclosing generative AI tools that made a
> substantial contribution. Paste/adapt this into the form at submission time.

## AI-usage statement

Generative AI tools (including Anthropic's Claude via Claude Code and OpenAI
Codex) were used substantially in preparing this work, under the direction and
full responsibility of the human authors:

- **Writing** — drafting and editing manuscript prose (abstract, section text, table
  captions), always reviewed and approved by the authors.
- **Code** — implementing and refactoring the benchmark harness, the failure-injection
  and routing-policy modules, the statistics utilities (bootstrap CIs and the exact
  sign-flip permutation test), and the analysis / reproduction scripts.
- **Analysis** — running the committed analysis scripts and cross-checking every
  reported aggregate against the committed CSV artifacts.
- **Internal review** — simulating an adversarial peer-review pass to surface
  weaknesses before submission.

The human authors conceived the research question and experimental design, ran the
real-Claude measured experiments, verified every reported number against committed
code and data, checked every citation against its primary source, and made all
scientific claims and final decisions. No AI-generated text, code, or result was
incorporated without human verification. The authors take full responsibility for
the content, including any errors.

## Conflict-of-interest note (separate OpenReview COI field)

The authors' affiliation is stated in the OpenReview form. The system under test in
this paper is Anthropic's Claude (`claude-sonnet-4-6`), and Anthropic/OpenAI tools
were also used as writing/coding assistants above; the authors have no financial
relationship with Anthropic or OpenAI beyond ordinary metered API usage. `[Authors
to confirm/complete any additional COI in the form.]`
