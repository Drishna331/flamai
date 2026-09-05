#!/usr/bin/env python3
"""Small isolated checks for the Part A script/metric audit."""

from __future__ import annotations

from pathlib import Path
import re
import unicodedata


HERE = Path(__file__).resolve().parent


def byte_tokens(text: str) -> int:
    return len(text.encode("utf-8"))


def old_word_count(line: str) -> int:
    return len(line.split(" "))


def fixed_word_count(line: str) -> int:
    return len(re.findall(r"\S+", line))


def corpus_lines(path: Path) -> list[str]:
    return [
        unicodedata.normalize("NFC", line.strip())
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    synthetic = "alpha  beta   gamma"
    old_fert = byte_tokens(synthetic) / old_word_count(synthetic)
    fixed_fert = byte_tokens(synthetic) / fixed_word_count(synthetic)
    print("multiple-space word bug")
    print(f"line={synthetic!r}")
    print(f"old_words={old_word_count(synthetic)} fixed_words={fixed_word_count(synthetic)}")
    print(f"old_tok_per_word={old_fert:.3f} fixed_tok_per_word={fixed_fert:.3f}")

    eng = corpus_lines(HERE / "corpus_flores_devtest" / "eng.txt")
    hin = corpus_lines(HERE / "corpus_flores_devtest" / "hin.txt")
    for lang, lines in [("eng", eng), ("hin", hin)]:
        lower_delta = (
            sum(byte_tokens(line.lower()) for line in lines) - sum(byte_tokens(line) for line in lines)
        )
        old_words = sum(old_word_count(line) for line in lines)
        fixed_words = sum(fixed_word_count(line) for line in lines)
        print(f"{lang} lowercase_byte_delta={lower_delta}")
        print(f"{lang} old_total_words={old_words} fixed_total_words={fixed_words}")

    print("conceptual denominator check")
    for lang, lines in [("eng", eng), ("hin", hin)]:
        total_tokens = sum(byte_tokens(line) for line in lines)
        total_words = sum(fixed_word_count(line) for line in lines)
        print(
            f"{lang} byte_tok_per_sentence={total_tokens / len(lines):.3f} "
            f"byte_tok_per_word={total_tokens / total_words:.3f}"
        )


if __name__ == "__main__":
    main()
