#!/usr/bin/env python3
"""Recompute serving capacity and goodput from the provided log."""

from __future__ import annotations

import csv
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    log = here.parent / "original_starter_kit" / "bench" / "bench_log.csv"
    with log.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    numeric = [
        "batch_size",
        "prompt_len",
        "gen_len",
        "num_requests",
        "wall_clock_s",
        "reported_tok_s",
        "preempted_seqs",
        "kv_cache_util",
        "ttft_ms_p50",
        "e2e_ms_p95",
    ]
    for row in rows:
        for key in numeric:
            row[key] = float(row[key])
        row["total_tokens"] = (row["prompt_len"] + row["gen_len"]) * row["num_requests"]
        row["reported_from_wall"] = row["total_tokens"] / row["wall_clock_s"]
        row["output_goodput_tok_s"] = row["gen_len"] * row["num_requests"] / row["wall_clock_s"]
        row["goodput_from_reported"] = row["reported_tok_s"] * row["gen_len"] / (
            row["prompt_len"] + row["gen_len"]
        )

    out = here / "serving_recomputed.csv"
    fields = list(rows[0])
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    kv_bytes_per_token = 28 * 8 * 128 * 2 * 2
    available_gb = 24 * 0.92 - 4.2 * 2 - 1.6
    max_tokens = available_gb * 1_000_000_000 / kv_bytes_per_token
    max_4096 = max_tokens / 4096

    print(f"kv_bytes_per_token={kv_bytes_per_token}")
    print(f"available_kv_GB_decimal={available_gb:.2f}")
    print(f"max_kv_tokens_decimal={max_tokens:.0f}")
    print(f"max_4096_sequences_decimal={max_4096:.2f}")
    print()
    display = [
        "batch_size",
        "prompt_len",
        "gen_len",
        "wall_clock_s",
        "reported_tok_s",
        "reported_from_wall",
        "output_goodput_tok_s",
        "goodput_from_reported",
        "preempted_seqs",
        "kv_cache_util",
        "ttft_ms_p50",
        "e2e_ms_p95",
    ]
    print(",".join(display))
    for row in rows:
        print(",".join(f"{row[key]:.6g}" for key in display))


if __name__ == "__main__":
    main()
