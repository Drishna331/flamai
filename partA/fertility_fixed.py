#!/usr/bin/env python3
"""Tokenizer fertility and compression audit with explicit denominators.

The original script in starter_kit/fertility.py averaged per-line
tokens/word and treated whitespace words as the main cross-language
denominator. This version keeps that smoke-test metric, but also reports
denominators that are more defensible for routing/cost decisions.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
import unicodedata

import regex as regex_mod


WORD_RE = re.compile(r"\S+")


@dataclass(frozen=True)
class LineStats:
    tokens: int
    words: int
    graphemes: int
    utf8_bytes: int
    chars: int


def load_tokenizer(spec: str):
    if spec == "byte_utf8":
        return lambda s: list(s.encode("utf-8"))

    if spec.startswith("spm:"):
        import sentencepiece as spm

        proc = spm.SentencePieceProcessor()
        proc.load(spec[4:])
        return proc.encode

    if spec.startswith("hf:"):
        from transformers import AutoTokenizer

        repo_id = spec[3:]
        tok = AutoTokenizer.from_pretrained(repo_id, use_fast=False)
        return lambda s: tok.encode(s, add_special_tokens=False)

    import tiktoken

    enc = tiktoken.get_encoding(spec)
    return enc.encode


def read_lines(path: Path, normalize: str = "NFC", lowercase: bool = False) -> list[str]:
    lines: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if normalize:
                line = unicodedata.normalize(normalize, line)
            if lowercase:
                line = line.lower()
            lines.append(line)
    if not lines:
        raise ValueError(f"{path} contains no non-empty lines")
    return lines


def measure_line(line: str, encode) -> LineStats:
    tokens = len(encode(line))
    words = len(WORD_RE.findall(line))
    graphemes = len(regex_mod.findall(r"\X", line))
    utf8_bytes = len(line.encode("utf-8"))
    chars = len(line)
    if min(words, graphemes, utf8_bytes, chars) <= 0:
        raise ValueError(f"cannot measure empty/wordless line: {line!r}")
    return LineStats(tokens, words, graphemes, utf8_bytes, chars)


def summarize(lines: list[str], encode) -> dict[str, float]:
    stats = [measure_line(line, encode) for line in lines]
    total_tokens = sum(s.tokens for s in stats)
    total_words = sum(s.words for s in stats)
    total_graphemes = sum(s.graphemes for s in stats)
    total_bytes = sum(s.utf8_bytes for s in stats)
    total_chars = sum(s.chars for s in stats)
    per_line_tok_word = sum(s.tokens / s.words for s in stats) / len(stats)
    return {
        "sentences": float(len(stats)),
        "tokens": float(total_tokens),
        "tok_per_sentence": total_tokens / len(stats),
        "tok_per_word_micro": total_tokens / total_words,
        "tok_per_word_line_avg": per_line_tok_word,
        "tok_per_grapheme": total_tokens / total_graphemes,
        "tok_per_utf8_byte": total_tokens / total_bytes,
        "tok_per_char": total_tokens / total_chars,
    }


def parse_corpus(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError("corpus must be LANG=PATH")
    lang, path = spec.split("=", 1)
    return lang, Path(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", action="append", required=True, type=parse_corpus)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--lowercase", action="store_true", help="replicate original lowercasing behavior")
    ap.add_argument("--normalization", default="NFC")
    args = ap.parse_args(argv)

    encode = load_tokenizer(args.tokenizer)
    print(f"tokenizer: {args.tokenizer}")
    print(
        "lang,sentences,tokens,tok_per_sentence,tok_per_word_micro,"
        "tok_per_word_line_avg,tok_per_grapheme,tok_per_utf8_byte,tok_per_char"
    )
    for lang, path in args.corpus:
        metrics = summarize(read_lines(path, args.normalization, args.lowercase), encode)
        print(lang + "," + ",".join(f"{metrics[k]:.6f}" for k in metrics))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
