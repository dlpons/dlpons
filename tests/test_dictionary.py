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
