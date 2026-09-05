# AI Team Intern Assignment - Audit Submission

This repository is my submission for **AI Team Intern Assignment - The Audit**.
It audits the previous intern's tokenizer and serving-capacity report, preserves
the starter kit, and includes reproducible scripts plus written answers.

## Repository layout

- `NOTEBOOK.md` - chronological hypothesis -> experiment -> result -> revision log.
- `AI_USAGE.md` - honest summary of where AI helped and where it misled or slowed me.
- `DEFENSE_PREP.md` - quick live-defense checklist of commands, numbers, and counterfactuals.
- `original_starter_kit/` - unmodified starter material used as the audit baseline.
- `partA/` - multilingual tokenizer corpus setup, corrected fertility analysis, audit evidence, and memo.
- `partB/` - KV-cache arithmetic, throughput/goodput reconciliation, and serving answers.
- `partC/memo.md` - decision memo for casual multilingual assistant replies.

## Reproduce the main results

Create an environment with the two declared dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Then run:

```bash
python3 partA/fetch_corpus.py
python3 partA/train_sentencepiece.py
python3 partA/analyze_tokenizers.py
python3 partA/audit_checks.py
python3 partB/capacity_reconciliation.py
```

The important generated files are:

- `partA/results/tokenizer_metrics.csv`
- `partA/results/ratios_vs_english.csv`
- `partB/serving_recomputed.csv`

## Headline conclusions

The original report's "Hindi costs about 6x" claim is not safe for routing or
capacity planning. On FLORES-200 devtest, an English-only byte-fallback
tokenizer makes Indic languages look 8.14x to 10.17x English by comparable
parallel sentence, while a multilingual SentencePiece tokenizer reduces that
sentence-level ratio to 0.95x to 1.08x English. The right production planning
metric is tokens per comparable request/task, not whitespace-word fertility.

For serving, the KV-cache math predicts about 25.7 concurrent 4096-token
sequences on the specified L4 setup. The benchmark log matches that prediction:
the long-context batch-24 row is near the limit with no preemptions, while batch
32 and batch 48 overfill KV cache, preempt sequences, and lose goodput. The
`reported_tok_s` column counts prompt plus generated tokens; the honest
generated-token goodput of the long-prompt batch-24 row is about 200.9 tok/s.

For the product decision, I recommend a small SFT pass on synthetic casualized
pairs, with prompt engineering as the baseline/fallback and a week-1 kill
criterion if reviewer preference or meaning preservation fails.
