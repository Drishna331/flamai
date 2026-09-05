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

On `alpha  beta   gamma`, the old count is 6 words while the fixed count is 3. With the deterministic byte tokenizer, the buggy old code reports 3.167 tokens/word while the fixed code reports 6.333 tokens/word. Direction: extra spaces make fertility look artificially better.

Claimed flaw 2: per-whitespace-word fertility is a weak cross-language serving denominator. With the byte tokenizer on FLORES devtest, Hindi is 2.18x English by tokens/word but 2.55x by tokens/parallel sentence and 3.92x by tokens/grapheme. The denominator changes the conclusion, because "word" is not held constant across scripts and languages.

Claimed flaw 3: the original sample corpus is too small. It used about 10 toy sentences; this run uses 1012 parallel sentences per language. The direction of the old Hindi-only conclusion is not enough for routing, because adding Kannada/Tamil/Telugu/Malayalam shows the largest ratios are not Hindi.

Suspicious but mostly harmless: NFC normalization is fine and should stay. In the audit check, NFC plus lowercasing changed English byte count by only 1 byte over 1012 sentences and Hindi by 0 bytes. Lowercasing is unnecessary for serving-cost measurement, but it is not the main distortion here.

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
