"""Short names for streets, and the names they are stored under."""

import re

# Typed phrase -> stored phrase
STREET_ALIASES = {
    "mass ave": "massachusetts ave",
    "comm ave": "commonwealth ave",
    "dot ave": "dorchester ave",
    "mlk jr": "martin luther king jr",
    "mlk": "martin luther king jr",
    "jfk st": "john f kennedy st",
    "mem dr": "memorial dr",
    "msgr": "monsignor",
    "av": "ave",
    "str": "st",
}

# Leading compass words
COMPASS = {"e": "east", "w": "west", "n": "north", "s": "south"}

# Longest phrase first
ALIAS_PATTERN = re.compile(
    r"\b("
    + "|".join(
        re.escape(typed) for typed in sorted(STREET_ALIASES, key=len, reverse=True)
    )
    + r")\b"
)


def expand_aliases(street: str) -> str:
    """Swaps typed short names for the stored ones.

    Args:
        street: A normalized street name.

    Returns:
        The name with each known short name written out.
    """
    return ALIAS_PATTERN.sub(lambda found: STREET_ALIASES[found.group(1)], street)


def compass_forms(street: str) -> list[str]:
    """Writes a street with its leading compass word both ways.

    Args:
        street: A normalized street name.

    Returns:
        The name, then the other spelling when it starts with a compass word.
    """
    words = street.split()

    if len(words) < 3:
        return [street]

    first = words[0]
    rest = " ".join(words[1:])
    if first in COMPASS:
        return [street, f"{COMPASS[first]} {rest}"]
    for short, long in COMPASS.items():
        if first == long:
            return [street, f"{short} {rest}"]
    return [street]
