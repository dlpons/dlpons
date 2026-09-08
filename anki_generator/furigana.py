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
            # Anki's {{furigana:}} template filter (kanji[reading] -> ruby)
            # scopes the base text by scanning back to the nearest space
            # (or start of string) before the "[" -- since Japanese text has
            # no spaces, without this leading space it swallows everything
            # back to the previous bracket (or start of field) as the ruby
            # base instead of just this kanji run.
            out.append(f" {part}[{next(groups)}]")
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


def _rendaku_person_suffix_reading(prev: Token, suffix: Token) -> str | None:
    """UniDic reads the bound suffix 人 ("-person/-people") as にん in
    isolation, but after a place/nationality/group name it's almost always
    voiced to じん via rendaku (日本人, 外国人, 中国人, ...), which a plain
    per-token reading doesn't capture. Only overrides the suffix's own
    reading -- and only when JMdict's compound entry confirms the *sole*
    difference from the naive concatenation is exactly this にん->じん
    voicing -- so it can't accidentally substitute an unrelated homograph
    reading for the whole span (that's what went wrong with a broader,
    less targeted version of this fix: it picked JMdict's first reading
    for 何時 -- いつ, "when" -- over UniDic's contextually-correct なんじ,
    "what time")."""
    if suffix.surface != "人":
        return None
    prev_reading = jaconv.kata2hira(prev.kana) if prev.kana and prev.kana != "*" else ""
    suffix_reading = jaconv.kata2hira(suffix.kana) if suffix.kana and suffix.kana != "*" else ""
    if not prev_reading or suffix_reading != "にん":
        return None

    combined = prev.surface + "人"
    entry = dictionary.best_entry(combined)
    if entry is None or combined not in entry.kanji_forms:
        return None

    target = prev_reading + "じん"
    if any(jaconv.kata2hira(k) == target for k in entry.kana_forms):
        return "じん"
    return None


def annotate(text: str) -> tuple[str, list[str]]:
    """Return (furigana_text, flags) for a word or full sentence."""
    flags: list[str] = []
    tokens = tokenize(text)
    out = []
    for i, tok in enumerate(tokens):
        if i > 0:
            override = _rendaku_person_suffix_reading(tokens[i - 1], tok)
            if override is not None:
                out.append(align_reading(tok.surface, override))
                continue
        out.append(furigana_for_token(tok, flags))
    return "".join(out), flags
