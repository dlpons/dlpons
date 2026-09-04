import pytest

from anki_generator.furigana import align_reading, annotate, has_kanji


def test_has_kanji():
    assert has_kanji("甘える")
    assert not has_kanji("ひらがな")
    assert not has_kanji("123 abc")


@pytest.mark.parametrize(
    "surface,reading,expected",
    [
        ("甘える", "あまえる", "甘[あま]える"),
        ("食べる", "たべる", "食[た]べる"),
        ("お金", "おかね", "お金[かね]"),
        ("学校", "がっこう", "学校[がっこう]"),
        ("取り扱い", "とりあつかい", "取[と]り扱[あつか]い"),
        ("私", "わたし", "私[わたし]"),
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
    assert text == "甘[あま]えるのは悪[わる]いことじゃない"
    assert flags == []


def test_annotate_no_kanji():
    text, flags = annotate("これはテストです")
    assert text == "これはテストです"
    assert flags == []
