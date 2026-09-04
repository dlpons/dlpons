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
| `Nuance` | LLM-generated (Claude), by design -- this is the one field that's a real dictionary lookup can't give you. Requires `ANTHROPIC_API_KEY`; left blank + flagged if it's not set, the call fails, or you pass `--no-llm`. |
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
`examples/entries.json`:

```json
[
  { "word": "甘える", "sentence": "子供の頃はよく母に甘えていた。" }
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

## Tests

```bash
pip install pytest
python -m pytest tests/
```

Tests cover the furigana alignment algorithm, pitch-accent classification
(including the textbook minimal-pair check), JMdict lookups, and the
AnkiConnect client (against a local mock HTTP server, no real Anki
required).
