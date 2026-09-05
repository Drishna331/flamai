# Part A - Tokenizer Audit Memo

## A1. Corpus

I used FLORES-200 devtest as the multilingual evaluation corpus. It is parallel, sentence-aligned text with 1012 non-empty sentences per language. The selected languages are English, Hindi, Kannada, Tamil, Telugu, Malayalam, Bengali, and Marathi, covering English, Hindi, four Dravidian languages, and two additional Indic languages. Corpus preparation is reproducible with:

```bash
python partA/fetch_corpus.py
```

Preprocessing: strip empty lines, Unicode NFC normalization during measurement, no lowercasing in the main result. I trained two local SentencePiece tokenizers: an English-only byte-fallback unigram tokenizer as the non-Indic-aware baseline, and a multilingual unigram tokenizer trained on all eight FLORES languages as the Indic-aware tokenizer.

```bash
python partA/train_sentencepiece.py
```

Caveat: FLORES is cleaner and more translation-like than production assistant traffic. It can show cross-script/tokenizer behavior on parallel sentences, but it cannot estimate slang, code-mixing, spelling variation, product-specific terms, or conversational reply length.

## A2. Script and Metric Audit

Claimed flaw 1: `line.split(" ")` miscounts words when there are repeated spaces. Evidence:

```bash
python partA/audit_checks.py
```

On `alpha  beta   gamma`, the old count is 6 words while the fixed count is 3. With the deterministic byte-token proxy, the buggy old code reports 3.167 tokens/word while the fixed code reports 6.333 tokens/word. Direction: empty fields from repeated spaces inflate the denominator, so fertility looks artificially better. On FLORES Hindi this is a small effect because the corpus is clean (`old_total_words=25649`, `fixed_total_words=25643`), but it is still a real parser bug for messier production text.

Claimed flaw 2: the script averages per-line ratios instead of reporting the corpus-level micro-average. A synthetic two-line check with one 101-word line and one long one-word line gives 14.995 tokens/word by line average but 2.245 by micro-average. Direction: short outlier lines get the same weight as long lines, so the metric is unstable as a corpus cost estimator. On clean FLORES the English difference is modest (6.062 old line-average byte tokens/word vs 6.032 fixed micro byte tokens/word), but the isolated test shows why the estimator itself is fragile.

Claimed flaw 3: per-whitespace-word fertility is the wrong routing denominator. With the byte-token proxy on FLORES devtest, Hindi is 2.18x English by tokens/word, 2.55x by tokens/parallel sentence, and 2.57x by Unicode character. The denominator changes the conclusion, because "word" and "character" do not hold the user task constant across languages. Serving cost is paid on prompt plus generated tokens per request, so the production analogue should be tokens per comparable request/task.

Claimed flaw 4: the original sample corpus is too small and too narrow. It used a toy English/Hindi sample; this run uses 1012 parallel sentences per language. The toy sample is acceptable for a smoke test, but not for the report's claim that no further measurement is needed. Adding Kannada/Tamil/Telugu/Malayalam also shows that the largest ratios are not Hindi.

Suspicious but mostly harmless: NFC normalization is fine and should stay. Lowercasing is unnecessary for serving-cost measurement, but in the audit check it changed English byte count by only 1 byte over 1012 sentences and Hindi by 0 bytes, so it is not the main distortion here. `random.seed(1337)` also looks suspicious in a benchmark script, but it is harmless because the script never calls a random API.

## A3. Corrected Analysis

Main command:

```bash
python partA/analyze_tokenizers.py
```

Outputs:

- `partA/results/tokenizer_metrics.csv`
- `partA/results/ratios_vs_english.csv`

Corrected headline ratios versus English:

| tokenizer | Hindi | Kannada | Tamil | Telugu | Malayalam | Bengali | Marathi |
|---|---:|---:|---:|---:|---:|---:|---:|
| English-only SentencePiece, tokens/parallel sentence | 8.14x | 9.03x | 10.17x | 8.50x | 9.92x | 8.42x | 8.58x |
| SentencePiece, tokens/parallel sentence | 0.97x | 1.01x | 0.99x | 1.00x | 1.08x | 0.96x | 0.95x |
| SentencePiece, tokens/word | 0.83x | 1.37x | 1.29x | 1.29x | 1.59x | 1.08x | 1.09x |
| SentencePiece, tokens/grapheme | 1.48x | 1.47x | 1.31x | 1.72x | 1.80x | 1.56x | 1.56x |

The single number I would use for routing and cost is tokens per parallel sentence, or its production equivalent: generated/request tokens at fixed task intent and quality. It best approximates the thing serving capacity pays for: total sequence tokens for the same user task. Per-word and per-grapheme are useful diagnostics, but they do not hold user intent constant.

## A4. Recommendation

Do not route Indic traffic using the original "Hindi costs 6x" claim. An English-only byte-fallback tokenizer makes Indic text 8.14x to 10.17x English by parallel sentence, while a multilingual SentencePiece tokenizer trained across these languages nearly removes the sentence-level penalty: 0.95x to 1.08x English across the measured languages.

Recommendation: use an Indic/multilingual tokenizer or model family for these languages, but budget from measured tokens per production request, not from whitespace-word fertility. The biggest caveat is domain shift: FLORES is not casual assistant traffic. The production metric I would monitor is generated plus prompt tokens per successful request, segmented by language and task type, with a weekly alert if any language exceeds English by more than 25% after controlling for prompt/output length policy.
