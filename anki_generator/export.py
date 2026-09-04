"""Write generated cards to a file Anki's File -> Import can read directly.

Anki (2.1.45+) recognizes '#directive:value' header lines in a text import
file to auto-set the deck, note type, separator and column mapping, so the
only manual step left is picking the file in the Import dialog -- no
column-mapping screen needed.
"""

from pathlib import Path

from .models import CardResult

FIELD_ORDER = ["Word", "Sentence", "PitchAccent", "Definition", "Nuance", "Audio", "Image"]


def _escape(value: str) -> str:
    # Import file is tab-separated, one note per line: neither character
    # can survive literally in a field.
    return value.replace("\t", " ").replace("\n", " ").replace("\r", " ")


def write_anki_import_file(
    results: list[CardResult],
    path: Path,
    deck: str,
    model: str,
    tags: list[str] | None = None,
) -> None:
    lines = [
        "#separator:tab",
        "#html:false",
        f"#deck:{deck}",
        f"#notetype:{model}",
        f"#columns:{chr(9).join(FIELD_ORDER)}",
    ]
    if tags:
        lines.append(f"#tags:{' '.join(tags)}")

    for result in results:
        fields = result.fields()
        row = "\t".join(_escape(fields[name]) for name in FIELD_ORDER)
        lines.append(row)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
