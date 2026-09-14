"""Name every rail line and branch once."""

# What each branch is called
BRANCHES: dict[str, dict[str, str]] = {
    "Green": {
        "Green-B": "B",
        "Green-C": "C",
        "Green-D": "D",
        "Green-E": "E",
    },
    "CR": {
        "CR-Fairmount": "Fairmount",
        "CR-Fitchburg": "Fitchburg",
        "CR-Foxboro": "Foxboro",
        "CR-Franklin": "Franklin",
        "CR-Greenbush": "Greenbush",
        "CR-Haverhill": "Haverhill",
        "CR-Kingston": "Kingston",
        "CR-Lowell": "Lowell",
        "CR-Needham": "Needham",
        "CR-NewBedford": "New Bedford",
        "CR-Newburyport": "Newburyport",
        "CR-Providence": "Providence",
        "CR-Worcester": "Worcester",
    },
}

LINES: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("Red", "RED", "Red Line", ("Red",)),
    ("Mattapan", "MATTAPAN", "Mattapan Line", ("Mattapan",)),
    ("Orange", "ORANGE", "Orange Line", ("Orange",)),
    ("Green", "GREEN", "Green Line", tuple(BRANCHES["Green"])),
    ("Blue", "BLUE", "Blue Line", ("Blue",)),
    ("CR", "COMMUTER", "Commuter Rail", tuple(BRANCHES["CR"])),
]

# The line each route is drawn under
LINE_OF: dict[str, str] = {}
for line_id, _, _, routes in LINES:
    for route in routes:
        LINE_OF[route] = line_id

# Every route that is a branch of a line
BRANCH_ROUTES: set[str] = set()
for branches in BRANCHES.values():
    BRANCH_ROUTES.update(branches)
