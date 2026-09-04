## Hi there 👋

<!--
**dlpons/dlpons** is a ✨ _special_ ✨ repository because its `README.md` (this file) appears on your GitHub profile.
-->

# Japanese Anki Card Generator

Turns a plain list of `{word, sentence}` pairs into fully-populated Anki
notes -- furigana, pitch accent, an English definition, and an LLM-written
"nuance" note -- and pushes them straight into Anki over
[AnkiConnect](https://foosoft.net/projects/anki-connect/). No CSV import
step.

Deck: `Mining`. Note type: `Devin1`, fields `Word, Sentence, PitchAccent,
Definition, Nuance, Audio, Image` (`Audio`/`Image` are always left blank
for you to fill in with HyperTTS / an image-search add-on).

## How each field is generated

| Field | Source |
|---|---|
| `Word` / `Sentence` | Tokenized with [UniDic](https://unidic.ninjal.ac.jp/) via `fugashi` (a real morphological dictionary, not character-by-character guessing), converted to `kanji[reading]` bracket notation. Readings for dictionary-form words are cross-checked against [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html) via `jamdict`; mismatches or unconfirmed readings are flagged in the CLI output rather than silently accepted. |
| `PitchAccent` | UniDic ships compiled pitch-accent data (the mora at which pitch drops) for most common words -- this is real accent-dictionary data, not an estimate. It's validated in `tests/test_pitch_accent.py` against the classic textbook triplet 端/箸/橋 (all はし, three different accents) plus 雨/花. You can optionally point `PITCH_ACCENT_TSV` at a local `word<TAB>reading<TAB>pitch_number` file (e.g. exported from the Kanjium pitch accent dataset) to override/extend coverage. If a word has no accent data anywhere, the field is left **blank** and it's called out in the "Flags" section of the output -- never guessed. |
| `Definition` | Quoted directly from JMdict glosses (first sense, up to 3 glosses). Left blank + flagged if the word isn't a JMdict headword. |
| `Nuance` | LLM-generated, by design -- this is the one field a real dictionary lookup can't give you. Two ways to fill it: (a) put a `"nuance"` key in the input entry yourself (e.g. written by a conversation with Claude) and the script uses it as-is, no API call; or (b) leave it out and set `ANTHROPIC_API_KEY` to have the script call the Anthropic API for you. If neither is available, it's left blank + flagged. |
| `Audio` / `Image` | Always blank. |

## Setup

### 1. Anki + AnkiConnect

1. Install [AnkiConnect](https://ankiweb.net/shared/info/2055492159) (code `2055492159`) via Anki's Tools → Add-ons → Get Add-ons.
2. Restart Anki and **leave it running** whenever you run this script.
3. Make sure the `Mining` deck and the `Devin1` note type (with fields
   `Word, Sentence, PitchAccent, Definition, Nuance, Audio, Image`, in
   that order) already exist in your collection.

### 2. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`jamdict-data` bundles a prebuilt JMdict/Kanjidic2 database (~40 MB), so
there's no separate dictionary download step. `unidic-lite` bundles a
small UniDic build; if you want fuller/more current vocabulary coverage,
swap it for the full dictionary:

```bash
pip uninstall unidic-lite
pip install unidic
python -m unidic download
```

### 3. Nuance generation (optional but recommended)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Without this, the script still runs and pushes notes -- `Nuance` is just
left blank and flagged so you can fill it in by hand.

### 4. Pitch accent override (optional)

UniDic's built-in accent data covers most common words. If you want wider
or independently-sourced coverage, set:

```bash
export PITCH_ACCENT_TSV=/path/to/accents.tsv
```

where each line is `word<TAB>reading(kana)<TAB>pitch_number[,pitch_number]`,
e.g. the format used by the community
[Kanjium pitch accent](https://github.com/mifunetoshiro/kanjium) dataset.

## Usage

Input is a JSON (or CSV) file of `{word, sentence}` entries -- see
`examples/entries.json`. Two optional keys let you override generated
fields: `"nuance"` skips the LLM call for that field entirely (e.g. if you
already have nuance text from a separate conversation with Claude), and
`"definition"` skips the JMdict lookup (e.g. for a kana-only word where
JMdict resolves to the wrong homograph, like bare あり picking 蟻 "ant"
instead of the intended slang "acceptable" sense):

```json
[
  { "word": "甘える", "sentence": "子供の頃はよく母に甘えていた。" },
  { "word": "切ない", "sentence": "彼女の気持ちを思うと切ない気持ちになる。", "nuance": "..." },
  { "word": "あり", "sentence": "じゃなかったらありだった。", "definition": "existing; alright; acceptable" }
]
```

```bash
# Preview what would be generated, without touching Anki:
python -m anki_generator --input examples/entries.json --dry-run

# Generate and push into Anki directly (Anki must be running with AnkiConnect):
python -m anki_generator --input examples/entries.json

# Generate a file for Anki's File > Import instead of using AnkiConnect
# (useful if the script isn't running on the same machine as Anki):
python -m anki_generator --input examples/entries.json --export mining_import.txt

# Add a tag, allow duplicates, skip the LLM nuance call:
python -m anki_generator --input my_words.json --tag mined-2026-09 --allow-duplicate --no-llm
```

`--export` writes a tab-separated file with `#deck:`/`#notetype:`/`#columns:`
header directives that Anki (2.1.45+) reads automatically, so importing it
is just File > Import > pick the file > Import -- no manual field mapping.

The script prints one line per note added, a final success/failure count,
and a "Flags" section listing anything it left blank or couldn't confirm
(missing JMdict entry, no pitch-accent data, nuance not generated, etc.)
so you know exactly what to review by hand.

## Troubleshooting

### Windows: `jamdict-data` install fails with `WinError 32`

```
error: [WinError 32] The process cannot access the file because it is being
used by another process: 'jamdict_data/jamdict.db.xz'
```

This is a real bug in `jamdict-data`'s own `setup.py` (v1.5), not your
machine: it opens `jamdict.db.xz` with `lzma.open(...)` and calls
`os.unlink()` on that same file *while the handle from the `with` block is
still open*. Deleting an open file is fine on Linux/Mac but always fails on
Windows -- so this reproduces 100% of the time on Windows, regardless of
antivirus, temp-folder location, or retries.

Workaround: pre-decompress the database yourself so the buggy branch never
runs (its guard is `if ZIPPED_DB exists and TARGET_DB doesn't exist`), then
build a wheel from the patched source and install that instead of letting
pip build the broken sdist:

```bash
pip download --no-binary jamdict-data --no-deps -d . jamdict-data==1.5
tar xzf jamdict_data-1.5.tar.gz && cd jamdict_data-1.5
python -c "
import lzma, os
with lzma.open('jamdict_data/jamdict.db.xz') as f:
    data = f.read()
with open('jamdict_data/jamdict.db', 'wb') as out:
    out.write(data)
os.remove('jamdict_data/jamdict.db.xz')
"
pip install wheel build
python -m build --wheel   # produces dist/jamdict_data-1.5-py3-none-any.whl
pip install dist/jamdict_data-1.5-py3-none-any.whl
pip install -r requirements.txt   # now a no-op for jamdict-data, installs the rest
```

The resulting wheel is pure Python + data (`py3-none-any`), so it's fine to
build it on any OS and copy the `.whl` file over to the Windows machine
that needs it.

## Tests

```bash
pip install pytest
python -m pytest tests/
```

Tests cover the furigana alignment algorithm, pitch-accent classification
(including the textbook minimal-pair check), JMdict lookups, and the
AnkiConnect client (against a local mock HTTP server, no real Anki
required).
