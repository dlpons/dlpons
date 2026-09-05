"""JMdict lookups via jamdict. This is the "real dictionary source" used
to cross-check readings and to source definitions (definitions are quoted
straight from JMdict glosses, not invented)."""

from dataclasses import dataclass
from functools import lru_cache

from jamdict import Jamdict


@dataclass
class DictEntry:
    kanji_forms: list[str]
    kana_forms: list[str]
    glosses: list[str]


@lru_cache(maxsize=1)
def _jam() -> Jamdict:
    return Jamdict()


@lru_cache(maxsize=4096)
def lookup(word: str) -> list[DictEntry]:
    """Look up `word` in JMdict. Returns [] if it isn't a known entry."""
    result = _jam().lookup(word)
    entries = []
    for e in result.entries:
        glosses = []
        for sense in e.senses:
            glosses.extend(g.text for g in sense.gloss)
        entries.append(
            DictEntry(
                kanji_forms=[k.text for k in e.kanji_forms],
                kana_forms=[k.text for k in e.kana_forms],
                glosses=glosses,
            )
        )
    return entries


def best_entry(word: str, reading: str | None = None) -> DictEntry | None:
    """Pick the entry whose kanji (or kana) form matches `word` exactly. A
    single kanji spelling often covers several JMdict entries with
    different readings and unrelated meanings (e.g. 分 = ふん "minute" /
    ぶ "one-tenth" / ぶん "portion"; 側 = そば "near" / がわ "side"). When
    `reading` is given (typically the reading we already determined via
    UniDic for furigana), prefer whichever matching entry actually has
    that reading, instead of JMdict's arbitrary first-listed homograph."""
    entries = lookup(word)
    if not entries:
        return None

    matches = [e for e in entries if word in e.kanji_forms or word in e.kana_forms]
    pool = matches or entries

    if reading:
        import jaconv

        target = jaconv.kata2hira(reading)
        for e in pool:
            if any(jaconv.kata2hira(k) == target for k in e.kana_forms):
                return e

    return pool[0]


def definition(
    word: str, lemma: str | None = None, reading: str | None = None, max_glosses: int = 3
) -> tuple[str, bool]:
    """Return (definition_text, found). Tries `word` first, then `lemma`
    (useful when the user typed an inflected form, e.g. "食べた"), using
    `reading` to disambiguate homographs when there's more than one JMdict
    entry for the same kanji spelling."""
    entry = best_entry(word, reading=reading)
    if entry is None and lemma and lemma != word:
        entry = best_entry(lemma, reading=reading)
    if entry is None or not entry.glosses:
        return "", False
    return "; ".join(entry.glosses[:max_glosses]), True


def reading_is_confirmed(word: str, kana_reading: str) -> bool:
    """True if `kana_reading` (hiragana or katakana) matches a reading
    JMdict records for `word`. Passes the reading into best_entry() so a
    homograph (e.g. 分's ぶん sense) is checked against its own matching
    entry rather than JMdict's arbitrary first-listed one."""
    import jaconv

    entry = best_entry(word, reading=kana_reading)
    if entry is None:
        return False
    target = jaconv.kata2hira(kana_reading)
    return any(jaconv.kata2hira(k) == target for k in entry.kana_forms)
