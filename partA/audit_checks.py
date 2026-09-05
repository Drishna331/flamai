#!/usr/bin/env python3
"""Evidence checks for the Part A script/metric audit.

This script intentionally uses only the Python standard library. It is not the
main tokenizer analysis; it isolates the claims made about the original
`fertility.py` implementation so each claim has a small before/after number.
"""

from __future__ import annotations

from pathlib import Path
import re
import unicodedata


HERE = Path(__file__).resolve().parent
LANGS = ["eng", "hin", "kan", "tam", "tel", "mal", "ben", "mar"]


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


def old_line_avg_fertility(lines: list[str]) -> float:
    return sum(byte_tokens(line.lower()) / old_word_count(line.lower()) for line in lines) / len(lines)


def fixed_micro_fertility(lines: list[str]) -> float:
    return sum(byte_tokens(line) for line in lines) / sum(fixed_word_count(line) for line in lines)


def tok_per_sentence(lines: list[str]) -> float:
    return sum(byte_tokens(line) for line in lines) / len(lines)


def tok_per_char(lines: list[str]) -> float:
    return sum(byte_tokens(line) for line in lines) / sum(len(line) for line in lines)


def print_row(name: str, old: float, fixed: float, unit: str = "") -> None:
    delta = fixed - old
    pct = (delta / old * 100.0) if old else 0.0
    suffix = f" {unit}" if unit else ""
    print(f"{name}: old={old:.6f}{suffix} fixed={fixed:.6f}{suffix} delta={delta:+.6f} ({pct:+.2f}%)")


def main() -> None:
    corpora = {lang: corpus_lines(HERE / "corpus_flores_devtest" / f"{lang}.txt") for lang in LANGS}
    eng = corpora["eng"]
    hin = corpora["hin"]

    print("claim 1: repeated-space word-count bug")
    synthetic = "alpha  beta   gamma"
    old_fert = byte_tokens(synthetic) / old_word_count(synthetic)
    fixed_fert = byte_tokens(synthetic) / fixed_word_count(synthetic)
    print(f"line={synthetic!r}")
    print(f"old_words={old_word_count(synthetic)} fixed_words={fixed_word_count(synthetic)}")
    print_row("synthetic_tok_per_word", old_fert, fixed_fert)
    print(
        "direction: empty fields from split(' ') inflate the denominator, "
        "making fertility look artificially lower."
    )

    print("\nclaim 2: the original per-line average is a fragile estimator")
    skewed = ["a " * 100 + "b", "antidisestablishmentarianism"]
    old_avg = sum(byte_tokens(line) / fixed_word_count(line) for line in skewed) / len(skewed)
    micro = sum(byte_tokens(line) for line in skewed) / sum(fixed_word_count(line) for line in skewed)
    print_row("skewed_line_average_vs_micro_average", old_avg, micro)
    print(
        "direction: line averaging gives a one-word outlier the same weight as "
        "a 101-word line; micro averaging better estimates corpus-level cost per word."
    )
    for lang in ["eng", "hin"]:
        old = old_line_avg_fertility(corpora[lang])
        fixed = fixed_micro_fertility(corpora[lang])
        print_row(f"{lang}_flores_old_line_avg_lowercase_vs_fixed_micro", old, fixed)

    print("\nclaim 3: whitespace words are the wrong routing denominator")
    eng_sentence = tok_per_sentence(eng)
    eng_word = fixed_micro_fertility(eng)
    eng_char = tok_per_char(eng)
    print("lang,sentence_ratio_vs_eng,word_ratio_vs_eng,char_ratio_vs_eng")
    for lang in LANGS:
        lines = corpora[lang]
        sentence_ratio = tok_per_sentence(lines) / eng_sentence
        word_ratio = fixed_micro_fertility(lines) / eng_word
        char_ratio = tok_per_char(lines) / eng_char
        print(f"{lang},{sentence_ratio:.3f},{word_ratio:.3f},{char_ratio:.3f}")
    print(
        "direction: the same byte-token proxy says Hindi is 2.55x English by "
        "parallel sentence but 2.18x by word and 2.57x by Unicode character. The choice "
        "of denominator changes the conclusion, so a routing metric must hold "
        "the user task/request constant."
    )

    print("\nclaim 4: the starter sample is too small and too narrow")
    sample_eng = corpus_lines(HERE.parent / "original_starter_kit" / "corpus_sample" / "eng_sample.txt")
    sample_hin = corpus_lines(HERE.parent / "original_starter_kit" / "corpus_sample" / "hin_sample.txt")
    sample_ratio = tok_per_sentence(sample_hin) / tok_per_sentence(sample_eng)
    flores_ratio = tok_per_sentence(hin) / tok_per_sentence(eng)
    print(f"starter_sample_lines={len(sample_eng)} flores_lines={len(eng)}")
    print_row("hindi_sentence_ratio_sample_vs_flores", sample_ratio, flores_ratio)
    print(
        "direction: the toy sample can only smoke-test the script. It cannot "
        "support the report's 'no further measurement needed' recommendation."
    )

    print("\nharmless/small-effect checks")
    for lang, lines in [("eng", eng), ("hin", hin)]:
        lower_delta = (
            sum(byte_tokens(line.lower()) for line in lines) - sum(byte_tokens(line) for line in lines)
        )
        old_words = sum(old_word_count(line) for line in lines)
        fixed_words = sum(fixed_word_count(line) for line in lines)
        print(f"{lang} lowercase_byte_delta={lower_delta}")
        print(f"{lang} old_total_words={old_words} fixed_total_words={fixed_words}")
    print("NFC normalization is retained: it is a reasonable corpus hygiene step.")
    print("random.seed(1337) is suspicious but harmless here: no random API is used by fertility.py.")


if __name__ == "__main__":
    main()
