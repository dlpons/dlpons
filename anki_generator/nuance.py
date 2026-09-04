"""Nuance-note generation. Unlike furigana/pitch-accent/definition, this
field is explicitly LLM-generated per spec: a concept-first explanation of
how the word actually feels/is used, for cases with no clean English
equivalent. Requires ANTHROPIC_API_KEY; if it's not set (or --no-llm is
passed), the field is left blank and flagged rather than faked.
"""

import os

_MODEL = os.environ.get("NUANCE_MODEL", "claude-sonnet-5")

_SYSTEM_PROMPT = (
    "You write short 'nuance' notes for a Japanese vocabulary Anki deck. "
    "The reader already has a dictionary definition; your job is to explain "
    "how the word actually feels and is used -- register, connotation, "
    "when a native speaker reaches for it over a near-synonym, and any gap "
    "with the English gloss. Write 2-4 plain, conversational sentences. No "
    "headers, no bullet points, no restating the dictionary definition "
    "verbatim."
)


def generate(word: str, definition: str, sentence: str) -> tuple[str, bool]:
    """Return (nuance_text, generated). generated=False means the field
    should be left blank and flagged (no API key, or the call failed)."""
    try:
        import anthropic
    except ImportError:
        return "", False

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "", False

    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = (
        f"Word: {word}\n"
        f"Dictionary definition: {definition or '(not found in JMdict)'}\n"
        f"Example sentence: {sentence}\n\n"
        "Write the nuance note."
    )
    try:
        response = client.messages.create(
            model=_MODEL,
            max_tokens=300,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception:
        return "", False

    text = "".join(block.text for block in response.content if hasattr(block, "text")).strip()
    if not text:
        return "", False
    return text, True
