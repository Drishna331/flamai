# Part B - Capacity Reconciliation

## B1. KV cache capacity

Given the model spec:

- layers = 28
- KV heads = 8
- head_dim = 128
- fp16 bytes = 2
- both K and V are cached

KV bytes per token:

```text
28 layers * 8 KV heads * 128 head_dim * 2 tensors(K,V) * 2 bytes = 114,688 bytes/token
```

Approximate KV budget, using decimal GB because the hardware spec says 24 GB:

```text
GPU budget after utilization = 24.0 * 0.92 = 22.08 GB
fp16 weights              = 4.2B params * 2 bytes = 8.40 GB
runtime overhead          = 1.60 GB
available KV cache        = 22.08 - 8.40 - 1.60 = 12.08 GB
max KV tokens             = 12.08e9 / 114,688 = 105,329 tokens
max 4096-token sequences  = 105,329 / 4096 = 25.7 sequences
```

This matches the log: the 3584+512 long-context rows are 4096 total tokens per request. Batch 24 reaches 0.93 KV utilization with zero preemptions. Batch 32 and 48 exceed the predicted capacity and show 7 and 23 preempted sequences, respectively, with KV utilization pinned at 0.97.

Command:

```bash
python partB/capacity_reconciliation.py
```

## B2. Long-context throughput anomaly

Naively, larger batch should increase throughput. In the long-context sweep, throughput rises through batch 24 and then falls:

| batch | reported tok/s | preempted seqs | KV util | TTFT p50 ms | E2E p95 ms |
|---:|---:|---:|---:|---:|---:|
| 16 | 1311.4 | 0 | 0.62 | 498.3 | 54602.1 |
| 24 | 1607.4 | 0 | 0.93 | 500.5 | 69221.3 |
| 32 | 1384.0 | 7 | 0.97 | 636.9 | 97465.7 |
| 48 | 1298.5 | 23 | 0.97 | 955.4 | 105427.5 |

Mechanism: batch 32/48 overfill the KV cache. The scheduler preempts sequences and loses effective work to recomputation or swapping, so total-token throughput drops while first-token and end-to-end latency jump.

Deployment change: cap admitted long-context concurrency at 24 sequences on one L4 for this model, or route long-context batches to a larger/multi-GPU pool. For this exact workload, a concurrency cap of 24 should preserve about 1607 total tok/s while eliminating preemptions. Relative to the observed batch-48 row, two waves of 24 would process 196,608 total tokens in about `2 * 61.16 = 122.32s`, or about 1607 tok/s, a 23.8% throughput improvement over 1298.5 tok/s, with much lower tail latency for admitted requests.

## B3. Misread column and honest goodput

The misread column is `reported_tok_s`. It is total prompt+generation tokens divided by wall time, not generated-output goodput. For long prompts, 3584 of 4096 tokens are prompt tokens, so 87.5% of the reported count is prefill/input work.

Batch-24 long-prompt goodput, from wall clock:

```text
24 requests * 512 generated tokens / 61.16 s = 200.9 generated tok/s
```

Same value from the reported throughput column:

```text
1607.4 reported tok/s * 512 generated tokens / 4096 total tokens = 200.9 generated tok/s
```

The report should have said: long prompts increase total-token accounting because prompt tokens are included in the throughput counter, but they do not imply better user-visible output capacity. The best stable long-context point in this log is batch 24, with about 201 generated tok/s and no preemptions. Batch 48 is not a 3200 tok/s capacity plan; it is already degraded by KV pressure and delivers only about 162 generated tok/s.

## B4. Counter to confirm mechanism

I would pull the serving stack's KV cache preemption/swap counter, e.g. `num_preemptions_total` or scheduler preemption count by reason. If the mechanism is right, it should stay at 0 through the long-context batch-24 row, then rise sharply at batch 32 and batch 48, aligning with `preempted_seqs = 7` and `23` and KV utilization near saturation.
