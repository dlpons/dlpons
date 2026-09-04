"""Furigana generation in kanji[reading] bracket notation.

Approach:
1. Tokenize with UniDic (fugashi) to get real dictionary readings per word,
   not a per-character guess.
2. For tokens whose surface form is itself a dictionary form, cross-check
   the reading against JMdict; flag it when JMdict disagrees or has no
   entry at all (still uses the UniDic reading, since UniDic is also a
   real morphological dictionary -- it just isn't independently confirmed).
3. Split each token's reading across its kanji/non-kanji runs with
   `align_reading`, which anchors on the non-kanji (kana) runs -- the
   okurigana is exact, so whatever reading is left over between anchors
   must belong to the kanji run next to it.
"""

import re

import jaconv

from . import dictionary
from .tokenizer import Token, tokenize

_KANJI_RUN = re.compile(r"[一-鿿々]+")


def has_kanji(text: str) -> bool:
    return bool(_KANJI_RUN.search(text))


def align_reading(surface: str, reading_hiragana: str) -> str:
    """Given a surface form and its full hiragana reading, return
    kanji[reading] bracket notation, e.g. align_reading("甘える", "あまえる")
    -> "甘[あま]える". Kana runs in `surface` are kept verbatim (not
    replaced by the possibly-normalized reading), only kanji runs get a
    bracketed reading.

    Raises ValueError if the reading can't be aligned against the surface
    (e.g. the reading doesn't actually contain the literal okurigana).
    """
    if not has_kanji(surface):
        return surface

    parts = re.split(f"({_KANJI_RUN.pattern})", surface)
    parts = [p for p in parts if p]

    pattern_pieces = []
    for part in parts:
        if _KANJI_RUN.fullmatch(part):
            pattern_pieces.append("(.+?)")
        else:
            pattern_pieces.append(re.escape(jaconv.kata2hira(part)))
    pattern = "^" + "".join(pattern_pieces) + "$"

    match = re.match(pattern, reading_hiragana)
    if match is None:
        raise ValueError(
            f"could not align reading {reading_hiragana!r} against surface {surface!r}"
        )

    groups = iter(match.groups())
    out = []
    for part in parts:
        if _KANJI_RUN.fullmatch(part):
            out.append(f"{part}[{next(groups)}]")
        else:
            out.append(part)
    return "".join(out)


def furigana_for_token(token: Token, flags: list[str]) -> str:
    surface = token.surface
    if not has_kanji(surface):
        return surface

    reading = jaconv.kata2hira(token.kana) if token.kana and token.kana != "*" else ""
    if not reading:
        flags.append(f'no reading found for "{surface}" -- left unbracketed')
        return surface

    if surface == token.lemma:
        if not dictionary.reading_is_confirmed(surface, reading):
            entry = dictionary.best_entry(surface)
            if entry is None:
                flags.append(f'"{surface}" not found in JMdict -- reading from UniDic only, unconfirmed')
            else:
                flags.append(
                    f'JMdict reading(s) {entry.kana_forms} for "{surface}" '
                    f"disagree with UniDic reading {reading!r} -- using UniDic"
                )
    else:
        # Inflected form (e.g. 食べた). Confirm the dictionary lemma is a
        # real word; the UniDic reading is trusted for the conjugation.
        if dictionary.best_entry(token.lemma) is None:
            flags.append(f'lemma "{token.lemma}" of "{surface}" not found in JMdict')

    try:
        return align_reading(surface, reading)
    except ValueError as exc:
        flags.append(str(exc))
        return surface


def annotate(text: str) -> tuple[str, list[str]]:
    """Return (furigana_text, flags) for a word or full sentence."""
    flags: list[str] = []
    out = [furigana_for_token(tok, flags) for tok in tokenize(text)]
    return "".join(out), flags
