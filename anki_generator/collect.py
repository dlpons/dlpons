"""Interactive daily word collection.

Type word/sentence pairs one at a time; leave Word blank to finish. Saves
to a JSON file that `python -m anki_generator --input <file>` then
processes (furigana, pitch accent, definitions, and -- if ANTHROPIC_API_KEY
is set -- nuance, fully automatically, no LLM chat round-trip needed).

    python -m anki_generator.collect
    python -m anki_generator.collect --output my_words.json
"""

import argparse
import json
from datetime import date
from pathlib import Path


def collect() -> list[dict]:
    entries: list[dict] = []
    print("Enter word/sentence pairs. Leave Word blank when you're done.\n")
    while True:
        word = input(f"[{len(entries) + 1}] Word: ").strip()
        if not word:
            break
        sentence = input("    Sentence: ").strip()
        entries.append({"word": word, "sentence": sentence})
    return entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Where to save the entries JSON (default: entries_YYYY-MM-DD.json)",
    )
    args = parser.parse_args(argv)
    output = args.output or Path(f"entries_{date.today().isoformat()}.json")

    entries = collect()
    if not entries:
        print("No entries collected -- nothing written.")
        return 1

    with output.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(entries)} entries to {output}")
    print(f"Next: python -m anki_generator --input {output} --dry-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
