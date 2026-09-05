#!/usr/bin/env python3
"""Fetch the FLORES-200 devtest files used for the tokenizer audit."""

from __future__ import annotations

from pathlib import Path
import tarfile
from urllib.request import urlopen


ARCHIVE_URL = "https://dl.fbaipublicfiles.com/nllb/flores200_dataset.tar.gz"

LANGS = {
    "eng": ("eng_Latn", "English"),
    "hin": ("hin_Deva", "Hindi"),
    "kan": ("kan_Knda", "Kannada"),
    "tam": ("tam_Taml", "Tamil"),
    "tel": ("tel_Telu", "Telugu"),
    "mal": ("mal_Mlym", "Malayalam"),
    "ben": ("ben_Beng", "Bengali"),
    "mar": ("mar_Deva", "Marathi"),
}


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "corpus_flores_devtest"
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / "flores200_dataset.tar.gz"
    should_download = True
    if archive.exists():
        with archive.open("rb") as f:
            should_download = f.read(2) != b"\x1f\x8b"
    if should_download:
        with urlopen(ARCHIVE_URL, timeout=120) as response, archive.open("wb") as f:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

    with tarfile.open(archive, "r:gz") as tf:
        members = {m.name.lstrip("./"): m for m in tf.getmembers()}
        for short, (flores_code, name) in LANGS.items():
            member_name = f"flores200_dataset/devtest/{flores_code}.devtest"
            member = members.get(member_name)
            if member is None:
                raise FileNotFoundError(member_name)
            extracted = tf.extractfile(member)
            if extracted is None:
                raise FileNotFoundError(member_name)
            text = extracted.read().decode("utf-8").strip() + "\n"
            path = out_dir / f"{short}.txt"
            path.write_text(text, encoding="utf-8")
            print(f"{short:>3} {flores_code:<9} {name:<10} {len(text.splitlines()):>4} lines -> {path}")


if __name__ == "__main__":
    main()
