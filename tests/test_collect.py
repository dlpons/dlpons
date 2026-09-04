import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from anki_generator.collect import main


def test_collect_writes_entries(tmp_path: Path):
    output = tmp_path / "entries.json"
    fake_input = StringIO("面白い\n今日の映画は面白かった。\n諦める\nもう諦めるしかない。\n\n")

    def fake_readline(prompt: str = "") -> str:
        line = fake_input.readline()
        if line == "":
            raise EOFError
        return line.rstrip("\n")

    with patch("builtins.input", side_effect=fake_readline):
        exit_code = main(["--output", str(output)])

    assert exit_code == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data == [
        {"word": "面白い", "sentence": "今日の映画は面白かった。"},
        {"word": "諦める", "sentence": "もう諦めるしかない。"},
    ]


def test_collect_no_entries_returns_error(tmp_path: Path):
    output = tmp_path / "entries.json"
    with patch("builtins.input", return_value=""):
        exit_code = main(["--output", str(output)])
    assert exit_code == 1
    assert not output.exists()
