import pytest

from anki_generator.pitch_accent import classify, count_morae, lookup_word


def test_count_morae_plain():
    assert count_morae("はし") == ["は", "し"]


def test_count_morae_youon():
    # きゃ is one mora, not two.
    assert count_morae("きゃく") == ["きゃ", "く"]


def test_count_morae_choon_and_sokuon_and_n():
    assert count_morae("がっこう") == ["が", "っ", "こ", "う"]
    assert count_morae("とうきょう") == ["と", "う", "きょ", "う"]
    assert count_morae("ほん") == ["ほ", "ん"]


@pytest.mark.parametrize(
    "drop,morae,expected",
    [
        (0, 2, "heiban"),
        (1, 2, "atamadaka"),
        (2, 2, "odaka"),
        (2, 3, "nakadaka"),
    ],
)
def test_classify(drop, morae, expected):
    assert classify(drop, morae) == expected


# The classic textbook minimal set: 端/箸/橋 are all はし but with three
# different accents. If this drifts, the UniDic accent data (or our
# classification of it) is broken.
@pytest.mark.parametrize(
    "word,drop,kind",
    [
        ("端", 0, "heiban"),
        ("箸", 1, "atamadaka"),
        ("橋", 2, "odaka"),
        ("雨", 1, "atamadaka"),
        ("花", 2, "odaka"),
    ],
)
def test_lookup_word_matches_known_accents(word, drop, kind):
    text, flags = lookup_word(word)
    assert flags == []
    assert f"[{drop}:" in text
    assert kind in text
