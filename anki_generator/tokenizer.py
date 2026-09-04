"""MeCab/UniDic tokenization, shared by the furigana and pitch-accent
lookups. UniDic is a real morphological dictionary (not a heuristic
guesser): each token carries its dictionary lemma, its orthographic kana
reading, and (for most common words) a compiled pitch-accent type."""

from dataclasses import dataclass
from functools import lru_cache

import fugashi


@dataclass
class Token:
    surface: str
    lemma: str
    kana: str  # orthographic reading, katakana, '*' if unknown
    accent_type: str  # e.g. "0", "1", "2,3", or "*" if not annotated
    pos: str


@lru_cache(maxsize=1)
def _tagger() -> fugashi.Tagger:
    return fugashi.Tagger()


def tokenize(text: str) -> list[Token]:
    tagger = _tagger()
    tokens = []
    for word in tagger(text):
        feat = word.feature
        tokens.append(
            Token(
                surface=word.surface,
                lemma=getattr(feat, "lemma", None) or word.surface,
                kana=getattr(feat, "kana", None) or "*",
                accent_type=getattr(feat, "aType", None) or "*",
                pos=getattr(feat, "pos1", None) or "*",
            )
        )
    return tokens
