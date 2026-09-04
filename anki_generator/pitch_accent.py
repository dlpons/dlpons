"""Pitch accent lookup.

Primary source: UniDic's `aType` feature, which is compiled pitch-accent
data (drop-mora position) attached to most common dictionary entries --
not a heuristic guess. It's cross-checked against the classic textbook
minimal set (箸=1, 橋=2, 端=0, 雨=1, 花=2) in tests/test_pitch_accent.py.

Optional secondary source: a local pitch-accent TSV in the "kanjium"
layout (word<TAB>reading<TAB>pitch_number[,pitch_number...]), if the user
points PITCH_ACCENT_TSV at one (see README "Pitch accent data" section).
When present it takes priority over UniDic for that word/reading pair.

If neither source has data for a word, the field is left blank and a flag
is raised -- per spec, we never estimate pitch accent.
"""

import os
from dataclasses import dataclass
from functools import lru_cache

import jaconv

from .tokenizer import tokenize

_SMALL_KANA = set("ゃゅょぁぃぅぇぉ")

_TYPE_NAMES = {
    "heiban": "heiban (平板)",
    "atamadaka": "atamadaka (頭高)",
    "nakadaka": "nakadaka (中高)",
    "odaka": "odaka (尾高)",
}


def count_morae(reading_hiragana: str) -> list[str]:
    morae: list[str] = []
    for ch in reading_hiragana:
        if ch in _SMALL_KANA and morae:
            morae[-1] += ch
        else:
            morae.append(ch)
    return morae


def classify(drop_position: int, mora_count: int) -> str:
    if drop_position == 0:
        return "heiban"
    if drop_position == 1:
        return "atamadaka"
    if drop_position == mora_count:
        return "odaka"
    return "nakadaka"


def format_pattern(reading_hiragana: str, drop_position: int) -> str:
    mora_count = len(count_morae(reading_hiragana))
    kind = classify(drop_position, mora_count)
    return f"{reading_hiragana} [{drop_position}: {_TYPE_NAMES[kind]}]"


@dataclass
class TsvSource:
    path: str
    table: dict[tuple[str, str], list[int]]

    @classmethod
    def load(cls, path: str) -> "TsvSource":
        table: dict[tuple[str, str], list[int]] = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line or line.startswith("#"):
                    continue
                cols = line.split("\t")
                if len(cols) < 3:
                    continue
                word, reading, pitches = cols[0], cols[1], cols[2]
                positions = [int(p) for p in pitches.split(",") if p.strip().isdigit()]
                if positions:
                    table[(word, jaconv.kata2hira(reading))] = positions
        return cls(path=path, table=table)


@lru_cache(maxsize=1)
def _tsv_source() -> "TsvSource | None":
    path = os.environ.get("PITCH_ACCENT_TSV")
    if not path or not os.path.exists(path):
        return None
    return TsvSource.load(path)


def lookup_word(word: str) -> tuple[str, list[str]]:
    """Return (pitch_accent_field_text, flags) for a single word."""
    flags: list[str] = []
    tokens = tokenize(word)
    if not tokens:
        flags.append(f'no tokens for "{word}" -- pitch accent left blank')
        return "", flags

    parts = []
    for tok in tokens:
        reading = jaconv.kata2hira(tok.kana) if tok.kana and tok.kana != "*" else ""
        if not reading:
            flags.append(f'no reading for "{tok.surface}" -- pitch accent left blank')
            continue

        tsv = _tsv_source()
        positions: list[int] | None = None
        if tsv is not None:
            positions = tsv.table.get((tok.surface, reading)) or tsv.table.get((tok.lemma, reading))

        if positions is None:
            if tok.accent_type in ("*", ""):
                flags.append(f'no pitch accent data for "{tok.surface}" -- left blank')
                continue
            positions = [int(p) for p in tok.accent_type.split(",") if p.strip().lstrip("-").isdigit()]
            if not positions:
                flags.append(f'no pitch accent data for "{tok.surface}" -- left blank')
                continue

        parts.append(" / ".join(format_pattern(reading, p) for p in positions))

    return "; ".join(parts), flags
