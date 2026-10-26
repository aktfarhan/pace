"""Read a user's saved place names in a question."""

import re

from backend.assistant.parse import ParsedQuery, read_model, read_question, words_of
from backend.core.clock import now_in_boston
from backend.geo.streets import Place

# Stand-in addresses the question reader reads as places
STAND_IN = "{}01 saved st"
STAND_IN_FOUND = re.compile(r"\b([1-9])01 saved st\b")

# Saved names one question can use
MAX_NAMES = 9

# Words before a place that mean going there
GOING = {"get", "go", "going", "head", "heading", "back", "me", "walk", "ride"}

# Words before a name that aren't part of it
LEADING = {"my", "the", "our"}

# Words around a saved name that still mean just that place
FILLER = GOING | LEADING | {",", "to"}


def name_key(text: str) -> str:
    """Writes a place name the way the question reader writes its words.

    Args:
        text: A saved name, or a place the reader found.

    Returns:
        Lowercase words joined by spaces.
    """
    words = [word for word in words_of(text) if re.search(r"[a-z0-9]", word)]
    while words and words[0] in LEADING:
        words.pop(0)
    return " ".join(words)


def name_spans(words: list[str], names: list[str]) -> list[tuple[int, int, str]]:
    """Finds each saved name in a question as whole words.

    Args:
        words: The question's words.
        names: Saved name keys.

    Returns:
        (start, end, name) for each name found.
    """
    taken = [False] * len(words)
    found = []

    # Longest names first
    for name in sorted(names, key=lambda one: -len(one.split())):
        parts = name.split()
        size = len(parts)

        # A name of only marks
        if size == 0:
            continue
        for start in range(len(words) - size + 1):
            end = start + size
            if words[start:end] != parts or any(taken[start:end]):
                continue
            taken[start:end] = [True] * size
            found.append((start, end, name))

    return sorted(found)[:MAX_NAMES]


def ends_a_longer_place(name: str, typed: ParsedQuery) -> bool:
    """Checks whether a saved name ends a longer place the reader found as typed.

    Args:
        name: A saved name key.
        typed: The reader's read of the question as typed.

    Returns:
        True for "school" in "somerville high school".
    """
    for end in (typed["origin"], typed["destination"]):
        if not end:
            continue
        match = re.search(rf"\b{re.escape(name)}\b", end)
        if match and any(word not in FILLER for word in end[: match.start()].split()):
            return True
    return False


def read_with_saved(query: str, spots: dict[str, Place]) -> ParsedQuery:
    """Reads a question, taking the user's saved names as places.

    Args:
        query: The user's question.
        spots: Saved name key -> where it is.

    Returns:
        The parsed query, with a saved name's key as that end.
    """
    # Most questions name no saved place and are read as typed
    words = words_of(query)
    found = name_spans(words, list(spots))
    if not found:
        return read_question(query)

    # A name that ends a longer place stays as typed
    typed, _ = read_model(query, now_in_boston())
    found = [span for span in found if not ends_a_longer_place(span[2], typed)]
    if not found:
        return read_question(query)

    # Each saved name becomes a stand-in address
    rewritten = []
    slots = {}
    last = 0
    for slot, (start, end, name) in enumerate(found, 1):
        rewritten += words[last:start]
        if start > 0 and words[start - 1] in GOING:
            if words[start - 1] == "back":
                rewritten.pop()
            rewritten.append("to")
        rewritten += STAND_IN.format(slot).split()
        slots[str(slot)] = name
        last = end
    rewritten += words[last:]

    parsed = read_question(" ".join(rewritten))
    for end in ("origin", "destination"):
        match = STAND_IN_FOUND.search(parsed[end] or "")
        if match is None:
            continue
        name = slots[match.group(1)]

        # A name inside a longer place
        rest = parsed[end].replace(match.group(0), " ").split()
        if all(word in FILLER for word in rest):
            parsed[end] = name
        else:
            parsed[end] = parsed[end].replace(match.group(0), name)
    return parsed
