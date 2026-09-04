"""Turns an Entry (word + sentence) into a fully populated CardResult."""

from . import dictionary, furigana, nuance, pitch_accent
from .models import CardResult, Entry
from .tokenizer import tokenize


def build_card(entry: Entry, use_llm: bool = True) -> CardResult:
    result = CardResult(entry=entry)

    word_furigana, word_flags = furigana.annotate(entry.word)
    result.word_furigana = word_furigana
    result.flags.extend(word_flags)

    sentence_furigana, sentence_flags = furigana.annotate(entry.sentence)
    result.sentence_furigana = sentence_furigana
    result.flags.extend(sentence_flags)

    pitch, pitch_flags = pitch_accent.lookup_word(entry.word)
    result.pitch_accent = pitch
    result.flags.extend(pitch_flags)

    lemma = tokenize(entry.word)[0].lemma if tokenize(entry.word) else entry.word
    definition, found = dictionary.definition(entry.word, lemma=lemma)
    result.definition = definition
    if not found:
        result.add_flag(f'"{entry.word}" not found in JMdict -- Definition left blank')

    if use_llm:
        nuance_text, generated = nuance.generate(entry.word, definition, entry.sentence)
        result.nuance = nuance_text
        if not generated:
            result.add_flag(
                f'nuance not generated for "{entry.word}" -- set ANTHROPIC_API_KEY, or fill in manually'
            )
    else:
        result.add_flag(f'nuance generation skipped (--no-llm) for "{entry.word}"')

    return result
