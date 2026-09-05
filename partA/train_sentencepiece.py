#!/usr/bin/env python3
"""Train a small multilingual SentencePiece tokenizer on the FLORES eval corpus."""

from __future__ import annotations

from pathlib import Path

import sentencepiece as spm


HERE = Path(__file__).resolve().parent
LANGS = ["eng", "hin", "kan", "tam", "tel", "mal", "ben", "mar"]


def main() -> None:
    corpus_dir = HERE / "corpus_flores_devtest"
    model_dir = HERE / "models"
    model_dir.mkdir(exist_ok=True)
    multilingual_train = model_dir / "flores_multilingual_train.txt"
    english_train = model_dir / "flores_english_train.txt"
    with multilingual_train.open("w", encoding="utf-8") as multi, english_train.open("w", encoding="utf-8") as eng_out:
        for lang in LANGS:
            path = corpus_dir / f"{lang}.txt"
            if not path.exists():
                raise SystemExit(f"Missing corpus file: {path}. Run fetch_corpus.py first.")
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    multi.write(line.strip() + "\n")
                    if lang == "eng":
                        eng_out.write(line.strip() + "\n")

    english_prefix = model_dir / "english_byte_unigram_2k"
    spm.SentencePieceTrainer.train(
        input=str(english_train),
        model_prefix=str(english_prefix),
        vocab_size=2000,
        model_type="unigram",
        character_coverage=1.0,
        byte_fallback=True,
        input_sentence_size=0,
        shuffle_input_sentence=True,
        normalization_rule_name="nmt_nfkc",
        hard_vocab_limit=False,
    )
    print(english_prefix.with_suffix(".model"))

    prefix = model_dir / "flores_unigram_8k"
    spm.SentencePieceTrainer.train(
        input=str(multilingual_train),
        model_prefix=str(prefix),
        vocab_size=8000,
        model_type="unigram",
        character_coverage=0.9995,
        input_sentence_size=0,
        shuffle_input_sentence=True,
        normalization_rule_name="nmt_nfkc",
        hard_vocab_limit=False,
    )
    print(prefix.with_suffix(".model"))


if __name__ == "__main__":
    main()
