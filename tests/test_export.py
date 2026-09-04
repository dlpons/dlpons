from pathlib import Path

from anki_generator.export import write_anki_import_file
from anki_generator.models import CardResult, Entry


def test_write_anki_import_file(tmp_path: Path):
    result = CardResult(entry=Entry(word="甘える", sentence="甘えていた。"))
    result.word_furigana = "甘[あま]える"
    result.sentence_furigana = "甘[あま]えていた。"
    result.pitch_accent = "あまえる [0: heiban]"
    result.definition = "to behave like a spoiled child"

    out = tmp_path / "import.txt"
    write_anki_import_file([result], out, deck="Mining", model="Devin1", tags=["mined"])

    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "#separator:tab"
    assert "#deck:Mining" in lines
    assert "#notetype:Devin1" in lines
    assert "#columns:Word\tSentence\tPitchAccent\tDefinition\tNuance\tAudio\tImage" in lines
    assert "#tags:mined" in lines

    data_line = lines[-1]
    cols = data_line.split("\t")
    assert cols[0] == "甘[あま]える"
    assert cols[2] == "あまえる [0: heiban]"


def test_write_anki_import_file_escapes_tabs_and_newlines(tmp_path: Path):
    result = CardResult(entry=Entry(word="x", sentence="y"))
    result.definition = "a\tb\nc"

    out = tmp_path / "import.txt"
    write_anki_import_file([result], out, deck="Mining", model="Devin1")

    data_line = out.read_text(encoding="utf-8").splitlines()[-1]
    assert data_line.count("\t") == 6  # exactly 7 columns, no stray tabs from the field
