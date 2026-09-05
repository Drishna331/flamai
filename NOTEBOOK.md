# NOTEBOOK.md

## 2026-09-01 - Assignment read and requirements audit

Hypothesis: the submission must audit the previous intern's report, not simply follow its conclusions.

Action: extracted and reviewed the assignment PDF and treated it as the grading specification.

Result: identified the required deliverables as `NOTEBOOK.md`, `AI_USAGE.md`, `partA`, `partB`, and `partC/memo.md`.

Part A requires a real multilingual corpus, evidence-backed script/metric audit, corrected analysis with two tokenizers and multiple denominators, and a one-page recommendation memo. Part B requires arithmetic checked against the serving log. Part C requires a labelled decision memo.

---

## 2026-09-02 - Starter kit preservation and corpus setup

Hypothesis: preserving the original files makes the audit defendable and allows every correction to be compared against the starter material.

Action: copied the starter kit into `original_starter_kit/`.

Result: original `fertility.py`, `REPORT_v0.md`, `bench/model_spec.md`, and `bench/bench_log.csv` are available for comparison.

Hypothesis: FLORES-200 devtest is a better audit corpus than the toy English/Hindi sample because it is parallel and multilingual.

Experiment:

```bash
python partA/fetch_corpus.py
```

Result: extracted 1012 non-empty devtest lines for English, Hindi, Kannada, Tamil, Telugu, Malayalam, Bengali, and Marathi.

Issue: the first implementation imported `requests` even when the archive was already present, which caused a slow/stuck import from the local dependency folder.

Revision: replaced the eager `requests` import with standard-library `urllib.request` and only read the gzip header, then made tar extraction tolerant of `./`-prefixed member names.

---

## 2026-09-03 - Tokenizer environment investigation

Hypothesis: local dependencies in `work/pydeps` would run with system `python3`.

Experiment:

```bash
PYTHONPATH=/Users/drishh/Documents/Codex/2026-09-04/do/work/pydeps python3 partA/analyze_tokenizers.py
```

Result: failed because the local NumPy wheel was CPython 3.12 while system Python was 3.11.

Revision: used the bundled Codex Python 3.12 runtime and created a clean dependency path excluding broken NumPy/Pandas shadow packages.

Hypothesis: `hf:google/mt5-small` would provide the multilingual tokenizer required for the comparison.

Experiment: attempted to run the analysis with the Hugging Face tokenizer.

Result: `transformers` import/cache resolution was too slow and fragile for a defense setting.

Revision: trained a deterministic local multilingual SentencePiece tokenizer from the FLORES corpus instead. This keeps the second tokenizer local, reproducible, and Indic-aware.

---

## 2026-09-04 - Corrected Part A analysis and audit checks

Experiments:

```bash
python partA/train_sentencepiece.py
python partA/analyze_tokenizers.py
python partA/audit_checks.py
```

Result: SentencePiece training used 1012 English sentences for the English-only byte-fallback baseline and 8096 total sentences for the multilingual tokenizer.

Finding: the English-only tokenizer makes Indic scripts cost about 8.14x to 10.17x English by parallel sentence.

Finding: the multilingual SentencePiece tokenizer reduces sentence-level ratios to 0.95x to 1.08x English.

The `audit_checks.py` experiment isolated the repeated-space word-count bug and showed why whitespace words are the wrong routing denominator.

Revision: the Part A memo recommends that production routing decisions use tokens per comparable request/task rather than whitespace-word fertility.

---

## 2026-09-04 - Part B capacity reconciliation

Hypothesis: the long-context throughput anomaly is caused by KV-cache saturation, rather than being evidence that larger batches always scale.

Experiment:

```bash
python partB/capacity_reconciliation.py
```

Result: KV cache is 114,688 bytes/token. With 12.08 decimal GB available for KV cache, the GPU holds about 105,329 KV tokens, or 25.72 concurrent 4096-token sequences.

The serving log matches this calculation: batch 24 has 0 preemptions and 0.93 KV utilization, while batch 32 and 48 preempt 7 and 23 sequences.

Revision: confirmed that `reported_tok_s` is prompt+output token throughput, not generated-token goodput. Batch-24 long-context generated goodput is about 200.9 tok/s.

---

## 2026-09-05 - Part C decision memo

Hypothesis: SFT is the best 3-week plan because it avoids introducing a second inference model and can be evaluated with the available reviewer budget.

Result: completed the decision memo recommending a small synthetic-pair SFT pass, with prompt engineering as the baseline/fallback.

The plan includes a week-1 kill criterion, numeric success thresholds, and reviewer-throughput arithmetic.
