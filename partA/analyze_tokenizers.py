#!/usr/bin/env python3
"""Run the tokenizer audit and write CSV summaries."""

from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PYTHON = sys.executable
TOKENIZERS = ["spm:models/english_byte_unigram_2k.model", "spm:models/flores_unigram_8k.model"]
LANGS = ["eng", "hin", "kan", "tam", "tel", "mal", "ben", "mar"]


def run(tokenizer: str, corpus_dir: Path) -> list[dict[str, str]]:
    print(f"running {tokenizer}...", file=sys.stderr, flush=True)
    tokenizer_arg = tokenizer
    if tokenizer.startswith("spm:"):
        tokenizer_arg = f"spm:{HERE / tokenizer[4:]}"
    cmd = [
        PYTHON,
        str(HERE / "fertility_fixed.py"),
        "--tokenizer",
        tokenizer_arg,
    ]
    for lang in LANGS:
        cmd.extend(["--corpus", f"{lang}={corpus_dir / f'{lang}.txt'}"])
    output = subprocess.check_output(cmd, text=True)
    csv_text = "\n".join(line for line in output.splitlines() if line and not line.startswith("tokenizer:"))
    rows = list(csv.DictReader(StringIO(csv_text)))
    for row in rows:
        row["tokenizer"] = tokenizer
    return rows


def main() -> None:
    corpus_dir = HERE / "corpus_flores_devtest"
    if not corpus_dir.exists():
        raise SystemExit("Run partA/fetch_corpus.py first.")

    rows = [row for tok in TOKENIZERS for row in run(tok, corpus_dir)]

    english = {row["tokenizer"]: row for row in rows if row["lang"] == "eng"}
    ratio_rows = []
    for row in rows:
        base = english[row["tokenizer"]]
        ratio_rows.append(
            {
                "tokenizer": row["tokenizer"],
                "lang": row["lang"],
                "sentence_token_ratio_vs_eng": f"{float(row['tok_per_sentence']) / float(base['tok_per_sentence']):.6f}",
                "word_ratio_vs_eng": f"{float(row['tok_per_word_micro']) / float(base['tok_per_word_micro']):.6f}",
                "grapheme_ratio_vs_eng": f"{float(row['tok_per_grapheme']) / float(base['tok_per_grapheme']):.6f}",
                "utf8_byte_ratio_vs_eng": f"{float(row['tok_per_utf8_byte']) / float(base['tok_per_utf8_byte']):.6f}",
            }
        )

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    metric_fields = ["tokenizer"] + [field for field in rows[0] if field != "tokenizer"]
    ratio_fields = list(ratio_rows[0])
    with (out_dir / "tokenizer_metrics.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=metric_fields)
        writer.writeheader()
        writer.writerows(rows)
    with (out_dir / "ratios_vs_english.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ratio_fields)
        writer.writeheader()
        writer.writerows(ratio_rows)

    for row in rows:
        print(",".join(row[field] for field in metric_fields))
    print()
    for row in ratio_rows:
        print(",".join(row[field] for field in ratio_fields))


if __name__ == "__main__":
    main()
