"""Command-line entry point.

    python -m anki_generator --input examples/entries.json
    python -m anki_generator --input examples/entries.json --dry-run
"""

import argparse
import csv
import json
import sys
from pathlib import Path

from .ankiconnect import AnkiConnectClient, AnkiConnectError
from .export import write_anki_import_file
from .generator import build_card
from .models import CardResult, Entry

DECK_NAME = "Mining"
MODEL_NAME = "Devin1"


def load_entries(path: Path) -> list[Entry]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [
                Entry(
                    word=row["word"].strip(),
                    sentence=row["sentence"].strip(),
                    nuance=(row.get("nuance") or "").strip(),
                )
                for row in reader
            ]

    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return [
        Entry(
            word=item["word"].strip(),
            sentence=item["sentence"].strip(),
            nuance=item.get("nuance", "").strip(),
        )
        for item in data
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, type=Path, help="JSON or CSV file with word/sentence entries")
    parser.add_argument("--deck", default=DECK_NAME, help=f"Anki deck name (default: {DECK_NAME})")
    parser.add_argument("--model", default=MODEL_NAME, help=f"Anki note type name (default: {MODEL_NAME})")
    parser.add_argument("--ankiconnect-url", default="http://127.0.0.1:8765")
    parser.add_argument("--dry-run", action="store_true", help="Generate cards but don't push to Anki")
    parser.add_argument(
        "--export",
        type=Path,
        help="Write generated cards to this file for Anki's File > Import, instead of pushing via AnkiConnect",
    )
    parser.add_argument("--no-llm", action="store_true", help="Skip nuance generation (leaves it blank)")
    parser.add_argument("--allow-duplicate", action="store_true")
    parser.add_argument("--tag", action="append", default=[], help="Tag to add to every note (repeatable)")
    args = parser.parse_args(argv)

    entries = load_entries(args.input)
    if not entries:
        print("No entries found in input file.", file=sys.stderr)
        return 1

    push_to_anki = not args.dry_run and not args.export
    client = AnkiConnectClient(url=args.ankiconnect_url)
    if push_to_anki:
        try:
            client.version()
        except AnkiConnectError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    ok = 0
    failed = 0
    all_flags: list[str] = []
    results: list[CardResult] = []

    for entry in entries:
        result = build_card(entry, use_llm=not args.no_llm)
        results.append(result)
        all_flags.extend(f"[{entry.word}] {flag}" for flag in result.flags)

        if not push_to_anki:
            print(f"--- {entry.word} ---")
            for name, value in result.fields().items():
                print(f"  {name}: {value}")
            ok += 1
            continue

        try:
            note_id = client.add_note(
                deck_name=args.deck,
                model_name=args.model,
                fields=result.fields(),
                tags=args.tag,
                allow_duplicate=args.allow_duplicate,
            )
            result.anki_note_id = note_id
            print(f"added {entry.word!r} -> note {note_id}")
            ok += 1
        except AnkiConnectError as exc:
            result.anki_error = str(exc)
            print(f"FAILED to add {entry.word!r}: {exc}", file=sys.stderr)
            failed += 1

    if args.export:
        write_anki_import_file(results, args.export, deck=args.deck, model=args.model, tags=args.tag)
        print(f"\nWrote {len(results)} note(s) to {args.export} -- Anki: File > Import, then pick this file.")

    print(f"\n{ok} succeeded, {failed} failed, {len(entries)} total.")
    if all_flags:
        print("\nFlags (things that were left blank or unconfirmed -- review these):")
        for flag in all_flags:
            print(f"  - {flag}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
