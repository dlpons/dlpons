"""Shared data structures."""

from dataclasses import dataclass, field


@dataclass
class Entry:
    """One input item: a word to mine plus an example sentence."""

    word: str
    sentence: str


@dataclass
class CardResult:
    """Everything generated for one Entry, plus any warnings raised along
    the way (missing dictionary entry, no pitch accent data, etc.)."""

    entry: Entry
    word_furigana: str = ""
    sentence_furigana: str = ""
    pitch_accent: str = ""
    definition: str = ""
    nuance: str = ""
    flags: list[str] = field(default_factory=list)
    anki_note_id: int | None = None
    anki_error: str | None = None

    def add_flag(self, message: str) -> None:
        self.flags.append(message)

    def fields(self) -> dict[str, str]:
        """Anki note fields, in the exact order of the Devin1 note type."""
        return {
            "Word": self.word_furigana,
            "Sentence": self.sentence_furigana,
            "PitchAccent": self.pitch_accent,
            "Definition": self.definition,
            "Nuance": self.nuance,
            "Audio": "",
            "Image": "",
        }
