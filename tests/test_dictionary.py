from anki_generator import dictionary


def test_definition_found():
    text, found = dictionary.definition("甘える")
    assert found
    assert "spoiled" in text or "fawn" in text


def test_definition_not_found():
    text, found = dictionary.definition("ぎゃおおおおん")
    assert not found
    assert text == ""


def test_definition_falls_back_to_lemma():
    # 食べた (past tense) isn't a JMdict headword; the lemma 食べる is.
    text, found = dictionary.definition("食べた", lemma="食べる")
    assert found
    assert "eat" in text


def test_reading_is_confirmed():
    assert dictionary.reading_is_confirmed("甘える", "あまえる")
    assert not dictionary.reading_is_confirmed("甘える", "あまいる")


def test_definition_disambiguates_homograph_by_reading():
    # 分 alone is ambiguous: ふん "minute", ぶ "one-tenth", or ぶん "portion".
    # Without a reading hint, JMdict's first-listed entry (ふん) wins, which
    # is wrong for e.g. 一か月分 ("a month's worth").
    default_text, _ = dictionary.definition("分")
    assert "minute" in default_text

    bun_text, found = dictionary.definition("分", reading="ぶん")
    assert found
    assert "portion" in bun_text or "part" in bun_text


def test_definition_disambiguates_side_by_reading():
    # 側 alone defaults to そば "near/beside"; がわ "side (of two parties)"
    # is a different JMdict entry entirely.
    gawa_text, found = dictionary.definition("側", reading="がわ")
    assert found
    assert "side" in gawa_text
