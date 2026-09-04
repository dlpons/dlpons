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
