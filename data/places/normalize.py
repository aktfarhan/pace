"""Shape street names for matching and for display."""

import re

# Type words and their USPS short forms
SUFFIXES = {
    "street": "st",
    "avenue": "ave",
    "road": "rd",
    "drive": "dr",
    "lane": "ln",
    "court": "ct",
    "place": "pl",
    "boulevard": "blvd",
    "terrace": "ter",
    "circle": "cir",
    "parkway": "pkwy",
    "highway": "hwy",
    "square": "sq",
    "turnpike": "tpke",
    "extension": "ext",
    "heights": "hts",
    "crossing": "xing",
    "mount": "mt",
    "saint": "st",
    "point": "pt",
    "plaza": "plz",
}

# For periods, apostrophes, and invisible characters
NOISE = re.compile(r"[.'\u2019\u00ad\u200b\u200c\ufeff\x7f]")


def normalize_street(name: str) -> str:
    """Turns a street name into the short form.

    Args:
        name: A street name.

    Returns:
        Lowercase, no periods, apostrophes, or hidden
        characters, with type words shortened.
    """
    words = NOISE.sub("", name.lower()).split()

    shortened = []
    for word in words:
        shortened.append(SUFFIXES.get(word, word))
    return " ".join(shortened)


def title_case(name: str) -> str:
    """Cases a name for display.

    Args:
        name: A name in capitals.

    Returns:
        Title case with possessives left.
    """
    return re.sub(r"'S\b", "'s", name.title())
