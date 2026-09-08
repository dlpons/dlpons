import re

import pytest

from anki_generator.furigana import align_reading, annotate, has_kanji

# Anki's actual {{furigana:}} template filter regex (rslib/src/template_filters.rs).
# It scopes the ruby base by scanning back to the nearest space (or string
# start) before "[" -- reproduced here so we can catch, as a regression test,
# any case where our bracket notation causes it to swallow more text than
# just the intended kanji run.
_ANKI_FURIGANA_RE = re.compile(r" ?([^ >]+?)\[(.+?)\]")


def _anki_ruby_bases(text: str) -> list[str]:
    """What Anki's real furigana filter would treat as each ruby's base text."""
    return [base for base, _reading in _ANKI_FURIGANA_RE.findall(text)]


def test_has_kanji():
    assert has_kanji("甘える")
    assert not has_kanji("ひらがな")
    assert not has_kanji("123 abc")


@pytest.mark.parametrize(
    "surface,reading,expected",
    [
        # Each kanji run gets a leading space: Anki's {{furigana:}} filter
        # scopes the ruby base by scanning back to the nearest space, so
        # without one it swallows preceding text instead of just the kanji.
        ("甘える", "あまえる", " 甘[あま]える"),
        ("食べる", "たべる", " 食[た]べる"),
        ("お金", "おかね", "お 金[かね]"),
        ("学校", "がっこう", " 学校[がっこう]"),
        ("取り扱い", "とりあつかい", " 取[と]り 扱[あつか]い"),
        ("私", "わたし", " 私[わたし]"),
        ("ひらがな", "ひらがな", "ひらがな"),
    ],
)
def test_align_reading(surface, reading, expected):
    assert align_reading(surface, reading) == expected


def test_align_reading_rejects_mismatched_okurigana():
    with pytest.raises(ValueError):
        align_reading("甘える", "あまえない")


def test_annotate_sentence():
    text, flags = annotate("甘えるのは悪いことじゃない")
    assert text == " 甘[あま]えるのは 悪[わる]いことじゃない"
    assert flags == []


def test_annotate_no_kanji():
    text, flags = annotate("これはテストです")
    assert text == "これはテストです"
    assert flags == []


def test_anki_furigana_filter_does_not_swallow_preceding_text():
    # Regression test for the actual bug hit in production: a kanji run
    # preceded by a long plain-text clause (no space -- Japanese has none)
    # must not have that clause end up as the ruby's base.
    text, _flags = annotate("バカにされたから、やり返してやった。")
    assert _anki_ruby_bases(text) == ["返"]


def test_anki_furigana_filter_does_not_swallow_adjacent_okurigana():
    # Two kanji runs separated by real okurigana (取り返す): the second
    # ruby's base must be just "返", not "り返".
    text, _flags = annotate("取り返す")
    assert _anki_ruby_bases(text) == ["取", "返"]


def test_anki_furigana_filter_handles_adjacent_kanji_runs():
    # Two kanji runs with nothing between them at all (一生出かけられません):
    # each ruby's base must stay scoped to its own run.
    text, _flags = annotate("一生出かけられません")
    assert _anki_ruby_bases(text) == ["一生", "出"]


def test_person_suffix_rendaku():
    # UniDic tokenizes 日本人 as 日本(にっぽん) + 人(にん), but the compound
    # is にほんじん/にっぽんじん -- 人 voices to じん after a place/nationality
    # name. Only the suffix's own reading should change.
    text, _flags = annotate("日本人が住んでいる")
    assert " 人[じん]" in text
    assert " 人[にん]" not in text


def test_person_suffix_rendaku_does_not_override_unrelated_homographs():
    # Regression check for an earlier, broader version of this fix that
    # accidentally let JMdict's first-listed reading for 何時 (いつ, "when")
    # override UniDic's contextually-correct なんじ ("what time") reading.
    text, _flags = annotate("何時に待ち合わせる？")
    assert "なん" in text or "何[なん]" in text
