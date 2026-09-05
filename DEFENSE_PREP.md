# Defense Prep

Use this as a quick checklist before the live 30-minute defense.

## Commands to be ready to run

```bash
python3 -m pip install -r requirements.txt
python3 partA/fetch_corpus.py
python3 partA/train_sentencepiece.py
python3 partA/analyze_tokenizers.py
python3 partA/audit_checks.py
python3 partB/capacity_reconciliation.py
```

## Numbers to re-derive without looking

- KV bytes per token: `28 layers * 8 KV heads * 128 head_dim * 2 K/V tensors * 2 fp16 bytes = 114,688 bytes/token`.
- Available KV memory: `24 * 0.92 - 4.2 * 2 - 1.6 = 12.08 GB`.
- Max 4096-token sequences: `12.08e9 / 114,688 / 4096 = 25.7`.
- Long-prompt batch-24 goodput: `24 * 512 / 61.16 = 200.9 generated tok/s`.
- Same goodput from reported throughput: `1607.4 * 512 / 4096 = 200.9 generated tok/s`.
- Multilingual tokenizer sentence-level ratios: about `0.95x` to `1.08x` English.
- English-only tokenizer sentence-level ratios: about `8.14x` to `10.17x` English.

## Likely counterfactuals

- If a grader changes repeated spaces in a corpus line, `audit_checks.py` shows why `split(" ")` is wrong: empty fields increase the word count and push tokens/word downward.
- If a grader asks why not use whitespace words, answer: routing cost is paid per request sequence, and translated words are not the same unit of work across languages.
- If a grader asks why FLORES is not enough, answer: it is parallel and multilingual, but cleaner than casual assistant traffic; production monitoring must track tokens per successful request by language and task type.
- If a grader asks why long prompts looked faster, answer: `reported_tok_s` counts prompt plus output tokens, so prefill tokens inflate the counter; user-visible decode goodput is much lower.
- If a grader asks why batch 32/48 regress, answer: 4096-token sequences exceed the KV-cache capacity predicted from the model spec, causing preemptions and tail-latency spikes.

## Weak spots to acknowledge honestly

- The local multilingual SentencePiece tokenizer is a defensible open baseline, not proof that any production model will behave exactly the same.
- FLORES does not cover slang, code-mixing, spelling variation, product jargon, or conversational style.
- The Part C plan has limited native-speaker coverage; the launch decision should explicitly accept or mitigate that risk.
