from unittest.mock import patch

from anki_generator.generator import build_card
from anki_generator.models import Entry


def test_prefilled_nuance_is_used_and_skips_api_call():
    entry = Entry(word="甘える", sentence="甘えていた。", nuance="hand-written nuance text")
    with patch("anki_generator.nuance.generate") as mock_generate:
        result = build_card(entry, use_llm=True)
    mock_generate.assert_not_called()
    assert result.nuance == "hand-written nuance text"
    assert not any("nuance" in flag for flag in result.flags)


def test_no_prefilled_nuance_falls_back_to_llm():
    entry = Entry(word="甘える", sentence="甘えていた。")
    with patch("anki_generator.nuance.generate", return_value=("generated text", True)) as mock_generate:
        result = build_card(entry, use_llm=True)
    mock_generate.assert_called_once()
    assert result.nuance == "generated text"


def test_prefilled_definition_is_used_and_skips_llm_call():
    entry = Entry(word="あり", sentence="じゃなかったらありだった。", definition="「よい」「OK」という意味です。")
    with patch("anki_generator.definition_ja.generate") as mock_generate:
        result = build_card(entry, use_llm=True)
    mock_generate.assert_not_called()
    assert result.definition == "「よい」「OK」という意味です。"
    assert not any("definition" in flag for flag in result.flags)


def test_no_prefilled_definition_falls_back_to_llm():
    entry = Entry(word="甘える", sentence="甘えていた。")
    with (
        patch("anki_generator.definition_ja.generate", return_value=("やさしい説明", True)) as mock_def,
        patch("anki_generator.nuance.generate", return_value=("nuance text", True)),
    ):
        result = build_card(entry, use_llm=True)
    mock_def.assert_called_once()
    assert result.definition == "やさしい説明"


def test_no_llm_and_no_prefilled_definition_leaves_it_blank():
    entry = Entry(word="甘える", sentence="甘えていた。")
    result = build_card(entry, use_llm=False)
    assert result.definition == ""
    assert any("definition generation skipped" in flag for flag in result.flags)
