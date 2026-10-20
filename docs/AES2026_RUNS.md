# AES 2026 follow-up runs

Three additions requested in the AAAI-27 reviews, run before the AES deadline (Oct 25, 2026).
Every command below writes **new** CSVs under `data/measured/`; none of them overwrites the
committed Sonnet results. Total expected cost is a few dollars.

## Setup (once)

```bash
git checkout aes-2026-controls-gemini
pip install -e ".[providers]"
```

Set API keys in your shell only (do not commit them or paste them into chats):

```bash
export ANTHROPIC_API_KEY=...   # controls on Sonnet
export GEMINI_API_KEY=...      # Gemini cross-model check
export OPENAI_API_KEY=...      # optional third provider
```

Before spending anything, check the plumbing offline:

```bash
python scripts/run_exp2_crossmodel.py --mock --models claude-sonnet-4-6 gemini-3.8-flash --runs 2 --control
```

## 1. No-injection controls (Sonnet 4.6)

Clean chains, same seeds and policies as the injected runs, so baseline execution error is
separated from injected-fault effects.

```bash
ORCHESTRATEBENCH_RAW_LOG=data/measured/raw/control_sonnet.jsonl \
  python -m orchestratebench.real_run --exp 2 --control --runs 10
#  -> data/measured/exp2_real_control.csv   (30 chains, depth 4)

python -m orchestratebench.real_run --exp 3 --control --runs 10 --depths 3,4,5,6,7
#  -> data/measured/exp3_real_control.csv   (150 chains, depths 3-7)
```

Expected: final-task success near 1.00 and cascade radius near 0. Anything lower is baseline
error that the injected-mode numbers should be read against.

## 2. Non-Claude cross-model check (Gemini)

Same five-mode arithmetic probe as the Sonnet/Opus/Haiku check, plus a matching control.

```bash
ORCHESTRATEBENCH_RAW_LOG=data/measured/raw/gemini.jsonl \
  python scripts/run_exp2_crossmodel.py --models gemini-3.8-flash --runs 30 --control
#  -> data/measured/exp2_gemini-3-8-flash.csv
#  -> data/measured/exp2_control_gemini-3-8-flash.csv
```

Thinking is set to the provider minimum by default for comparability with the Claude runs.
If the run prints a warning about responses with no visible text, rerun with a larger budget,
for example `ORCHESTRATEBENCH_NONCLAUDE_MAX_TOKENS=2048`, and report the setting used.
Controls: `ORCHESTRATEBENCH_GEMINI_THINKING` (`minimal`, `low`, an integer budget, or `off`)
and `ORCHESTRATEBENCH_OPENAI_REASONING` (`minimal`, `low`, or `off`).

Optional OpenAI run: replace the model with an OpenAI id, e.g. `--models gpt-6.1-sol`.

## 3. Second annotator for the Exp 1 routing diagnostic

```bash
python scripts/make_annotation_sheet.py --out routing_annotation_sheet.xlsx
# annotator fills column C blind (no access to gold labels), then:
python scripts/compute_kappa.py routing_annotation_sheet.xlsx
```

Reports Cohen's kappa overall and for aligned and adversarial cases, and lists disagreements
for adjudication.

## After the runs

Send back the new CSVs (and the `raw/` JSONL logs if you want trace analysis). The raw logs
contain only prompts and model outputs, never keys.
