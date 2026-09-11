"""Name every rail line once."""

LINES: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("Red", "RED", "Red Line", ("Red",)),
    ("Mattapan", "MATTAPAN", "Mattapan Line", ("Mattapan",)),
    ("Orange", "ORANGE", "Orange Line", ("Orange",)),
    (
        "Green",
        "GREEN",
        "Green Line",
        ("Green-B", "Green-C", "Green-D", "Green-E"),
    ),
    ("Blue", "BLUE", "Blue Line", ("Blue",)),
    (
        "CR",
        "COMMUTER",
        "Commuter Rail",
        (
            "CR-Fairmount",
            "CR-Fitchburg",
            "CR-Foxboro",
            "CR-Franklin",
            "CR-Greenbush",
            "CR-Haverhill",
            "CR-Kingston",
            "CR-Lowell",
            "CR-Needham",
            "CR-NewBedford",
            "CR-Newburyport",
            "CR-Providence",
            "CR-Worcester",
        ),
    ),
]

# The line each route is drawn under
LINE_OF: dict[str, str] = {}
for line_id, _, _, routes in LINES:
    for route in routes:
        LINE_OF[route] = line_id
