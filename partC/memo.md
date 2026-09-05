# Part C - Decision Memo

## Recommendation

Choose path (a): a small SFT pass on synthetic "casualized" response pairs, with prompt engineering as the baseline and fallback. I would not launch a separate inference-time rewriter in the first 3 weeks because it adds latency, another model to monitor, and a new failure mode where meaning changes after the main model answers.

## Assumptions

- Target launch languages: Hindi, Kannada, Tamil, Telugu, Bengali, Marathi.
- One A100-80GB can train a LoRA/QLoRA style adapter for the current assistant model within the 2-week compute window.
- We can generate synthetic pairs locally from existing model outputs plus deterministic style instructions, then sample-review the result.
- The native-speaker reviewer covers Hindi and Kannada directly; for the other four languages we use automatic checks plus small bilingual spot checks, and treat launch as gated until product accepts that risk.

## Back-of-envelope arithmetic

Data volume: start with 1,000 prompts per language across support, chit-chat, refusals, task completion, and product-domain answers. That is 6,000 prompt-response pairs. At roughly 250 input tokens and 120 output tokens per example, the SFT set is about `6,000 * 370 = 2.22M` tokens per epoch. Three epochs is about 6.7M training tokens, comfortably inside one A100-80GB for adapter tuning.

Reviewer throughput: 10 h/week for 3 weeks gives 30 reviewer-hours. At 60 examples/hour for accept/reject plus short notes, that is 1,800 reviewed examples. I would allocate 600 Hindi, 600 Kannada, 300 cross-language prompt-level checks, and 300 regression/refusal checks. That is enough to estimate launch quality for the two covered languages and catch broad instruction-following regressions, but not enough to certify all six languages equally.

Serving cost: SFT has no extra inference hop. A rewriter of <=1B would add one more decode pass to every response. Even if small, a 120-token rewrite at production scale adds latency and operational cost exactly where the product is trying to improve conversational quality.

## Success metric

On a 300-example hidden launch set per language, require:

- >=80% native-speaker preference for SFT over current model on "casual but still helpful" style for Hindi and Kannada.
- <=2% meaning-change or safety-regression rate on reviewed Hindi/Kannada examples.
- No worse than current model on task completion in at least 95% of automatically checked examples across all six languages.

## Kill criterion

Kill SFT by the end of week 1 if a 200-example Hindi+Kannada pilot fails to reach 65% reviewer preference or shows >3% meaning-change/safety regressions. In that case, ship prompt-engineering-only for launch review and continue collecting human-written casual examples before training.

## Day-1 experiment

Build a 120-example pilot: 20 prompts per language, covering the six highest-risk styles. Generate current-model answers, create synthetic casualized targets with strict meaning-preservation instructions, train a tiny adapter smoke run, and have the reviewer blind-rank current vs prompt-only vs SFT for Hindi and Kannada. The goal is not final quality; it is to discover whether SFT moves the right perceptual metric without breaking meaning.
