"""Check the eval files: schema, references, and coherence."""

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import psycopg

from backend.geocode import distance_km, root_id
from data.schema import connect

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "eval"
REFUSAL_PATH = ROOT / "prompts" / "refusal.md"

# The fields each file's rows must have, in order
SEED_FIELDS = [
    "id",
    "query",
    "domain",
    "style",
    "gold_answer",
    "gold_sources",
    "expected_action",
    "expected_risk",
    "notes",
]
PLACES_FIELDS = ["id", "query", "expected", "display", "notes"]
RETRIEVAL_FIELDS = ["id", "query", "expected", "resolve", "notes"]

DOMAINS = {
    "route",
    "alert",
    "parking-rules",
    "parking-sign",
    "schedule",
    "info",
    "off-topic",
}
STYLES = {"formal", "casual", "typo", "abbrev", "adversarial"}
ACTIONS = {"answer", "refuse"}
RISKS = {"low", "mid", "high", "n/a"}

# What share of the seed set each domain should be
DOMAIN_TARGETS = {
    "route": 0.30,
    "alert": 0.15,
    "parking-rules": 0.15,
    "schedule": 0.15,
    "info": 0.10,
    "parking-sign": 0.10,
    "off-topic": 0.05,
}
STYLE_TARGETS = {
    "casual": 0.50,
    "formal": 0.25,
    "typo+abbrev": 0.15,
    "adversarial": 0.10,
}

# Allowed drift from a target share
SHARE_SLACK = 0.03

# Two ids further apart than this are different places
SAME_PLACE_METERS = 300

# The wider limit, for areas
SAME_AREA_METERS = 1500
AREA_KINDS = {"neighborhood", "town"}

# The lookahead skips highway names like I-93 and US-1
PRONOUNS = re.compile(r"\b(I|we|our|my|us)\b(?!-\d)", re.IGNORECASE)

# A row id mentioned in a note
CITATION = re.compile(r"\b([qpr]-\d{4})\b")

# An id with a prefix
NAMESPACED = re.compile(r"^[a-z-]+:")

# The only prefixes gold_sources is allowed to use
SOURCE_SCHEMES = ("mbta://", "bos://", "cam://", "gbfs://", "signs/")

# The prompt files
PROMPTS_DIR = ROOT / "prompts"


def load(name: str) -> list[dict[str, Any]]:
    """Reads one eval file into rows.

    Args:
        name: The file's name ("seed").

    Returns:
        One dict per line.
    """
    path = EVAL_DIR / f"{name}.jsonl"
    if not path.exists():
        raise SystemExit(f"{path} is missing")

    rows = []
    with path.open(encoding="utf-8") as eval_file:
        for number, line in enumerate(eval_file, start=1):
            # Skip blank lines
            if not line.strip():
                continue

            # Stop on a broken line and say which one
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise SystemExit(f"{name}.jsonl line {number} is not JSON: {error}")

            # Every row needs an id
            if not isinstance(row, dict) or "id" not in row:
                raise SystemExit(f"{name}.jsonl line {number} has no id")

            rows.append(row)
    return rows


def load_templates() -> list[str]:
    """Reads the refusal templates the golds are allowed to use.

    Returns:
        One template per block, or an empty list if missing file.
    """
    if not REFUSAL_PATH.exists():
        return []

    text = REFUSAL_PATH.read_text(encoding="utf-8")

    # Each code block holds one template
    templates = []
    for block in re.findall(r"```\n(.*?)\n```", text, re.DOTALL):
        templates.append(block.strip())
    return templates


def normalize(query: str) -> str:
    """Strips a query down for duplicate comparison.

    Args:
        query: The row's query.

    Returns:
        Lowercase with punctuation removed.
    """
    return re.sub(r"[^a-z0-9 ]", "", query.lower()).strip()


def fills(template: str, gold: str) -> bool:
    """Checks whether a gold answer is one of the refusal templates.

    Args:
        template: One refusal template, which may hold a blank like {source_link}.
        gold: The row's gold answer.

    Returns:
        True when the gold matches, with any text allowed in the blank.
    """
    pattern = re.escape(template)
    for placeholder in (r"\{place\}", r"\{city\}", r"\{source_link\}"):
        pattern = pattern.replace(placeholder, ".+")
    return re.fullmatch(pattern, gold) is not None


def check_shape(name: str, rows: list, prefix: str, fields: list[str]) -> list[str]:
    """Checks ids, field order, and duplicate queries for one file.

    Args:
        name: The file's name.
        rows: Its rows.
        prefix: The letter every id starts with.
        fields: The field names every row carries, in order.

    Returns:
        One message per problem.
    """
    problems = []

    # Read the id numbers
    numbers = []
    for row in rows:
        parts = row["id"].split("-")

        # Ids must look like q-0001
        if len(parts) != 2 or parts[0] != prefix or not parts[1].isdigit():
            problems.append(f"{name}: {row['id']!r} is not shaped {prefix}-0001")
            continue
        numbers.append(int(parts[1]))

    # Check for repeats, and ordering
    seen_numbers = set()
    for index, number in enumerate(numbers):
        if number in seen_numbers:
            problems.append(f"{name}: {prefix}-{number:04d} appears twice")
        seen_numbers.add(number)
        if index and number < numbers[index - 1]:
            problems.append(f"{name}: {prefix}-{number:04d} sits out of order")

    # Same fields, same order
    for row in rows:
        # Ignore the image field
        present = [key for key in row if key != "image"]
        if present != fields:
            problems.append(f"{name}: {row['id']} field set is {present}")

    # No question appears twice
    seen = Counter(normalize(row.get("query", "")) for row in rows)
    for query, count in seen.items():
        if count > 1:
            problems.append(f"{name}: {count} rows share the query {query!r}")

    return problems


def check_seed(rows: list, templates: list[str]) -> list[str]:
    """Checks seed rows for valid values and gold-versus-action coherence.

    Args:
        rows: The seed rows.
        templates: The refusal templates a refusing gold may use.

    Returns:
        One message per problem.
    """
    problems = []
    for row in rows:
        # The row's fields
        row_id = row["id"]
        domain = row.get("domain")
        style = row.get("style")
        action = row.get("expected_action")
        risk = row.get("expected_risk")
        gold = row.get("gold_answer", "")
        sources = row.get("gold_sources", [])
        notes = row.get("notes", "")

        if domain not in DOMAINS:
            problems.append(f"seed: {row_id} domain {domain!r}")
        if style not in STYLES:
            problems.append(f"seed: {row_id} style {style!r}")
        if action not in ACTIONS:
            problems.append(f"seed: {row_id} expected_action {action!r}")
        if risk not in RISKS:
            problems.append(f"seed: {row_id} expected_risk {risk!r}")

        if not gold.strip():
            problems.append(f"seed: {row_id} has no gold_answer")
        if not notes.strip():
            problems.append(f"seed: {row_id} has no notes")

        # Source prefixes
        for source in sources:
            if not source.startswith(SOURCE_SCHEMES):
                problems.append(f"seed: {row_id} cites {source!r}, an unknown scheme")

        # Refusal rows
        if action == "refuse":
            if sources:
                problems.append(f"seed: {row_id} refuses but lists gold_sources")
            if risk != "n/a":
                problems.append(f"seed: {row_id} refuses but risk is not n/a")

            # The matching wording comes from refusal.md
            if templates:
                matched = False
                for template in templates:
                    if fills(template, gold):
                        matched = True
                        break
                if not matched:
                    problems.append(f"seed: {row_id} gold matches no refusal template")
        elif action == "answer" and not sources:
            problems.append(f"seed: {row_id} answers but cites nothing")

        # The sign photo
        image = row.get("image", "")
        if bool(image) != (domain == "parking-sign"):
            problems.append(f"seed: {row_id} image field and domain disagree")
        if image:
            number = row_id.split("-")[-1]
            if image != f"signs/{number}.jpg":
                problems.append(
                    f"seed: {row_id} image {image!r} is not signs/{number}.jpg"
                )

    return problems


def check_places(rows: list) -> list[str]:
    """Checks places rows for valid ids, a matching display, and notes.

    Args:
        rows: The places rows.

    Returns:
        One message per problem.
    """
    problems = []
    for row in rows:
        expected = row.get("expected", [])
        display = row.get("display", "")
        notes = row.get("notes", "")

        # An empty expected means "no match"
        if (not expected) != (display == "no match"):
            problems.append(f"places: {row['id']} display and expected disagree")
        if not display.strip():
            problems.append(f"places: {row['id']} has no display")
        if not notes.strip():
            problems.append(f"places: {row['id']} has no notes")

        # Ids drop the alias index
        for place_id in expected:
            # Addresses and streets key on a label
            if NAMESPACED.match(place_id) and root_id(place_id) != place_id:
                problems.append(f"places: {row['id']} {place_id} keeps an alias index")

        # No id listed twice
        if len(expected) != len(set(expected)):
            problems.append(f"places: {row['id']} lists an id twice")

    return problems


def check_retrieval(rows: list) -> list[str]:
    """Checks retrieval rows for chunk ids, notes, and a matching resolve flag.

    Args:
        rows: The retrieval rows.

    Returns:
        One message per problem.
    """
    problems = []
    for row in rows:
        expected = row.get("expected", [])
        resolve = row.get("resolve")
        notes = row.get("notes", "")

        # Every row names at least one chunk
        if not expected:
            problems.append(f"retrieval: {row['id']} expects nothing")
        if len(expected) != len(set(expected)):
            problems.append(f"retrieval: {row['id']} lists a chunk twice")
        if not notes.strip():
            problems.append(f"retrieval: {row['id']} has no notes")

        # The resolve flag must be true or false
        if not isinstance(resolve, bool):
            problems.append(
                f"retrieval: {row['id']} resolve is {resolve!r}, not a boolean"
            )
            continue

        # Parking rows
        parking = False
        for chunk_id in expected:
            if chunk_id.startswith("street-cleaning:"):
                parking = True
                break
        if parking and resolve:
            problems.append(f"retrieval: {row['id']} is parking but resolve is on")
        if not parking and not resolve:
            problems.append(f"retrieval: {row['id']} is transit but resolve is off")

    return problems


def check_prose(files: dict[str, list]) -> list[str]:
    """Checks notes and golds for first person.

    Args:
        files: Every file's rows, keyed by name.

    Returns:
        One message per problem.
    """
    problems = []
    for name, rows in files.items():
        for row in rows:
            for field in ("notes", "gold_answer"):
                if PRONOUNS.search(row.get(field, "")):
                    problems.append(f"{name}: {row['id']} uses first person in {field}")
    return problems


def check_citations(files: dict[str, list]) -> list[str]:
    """Checks that every row id named in a note still exists.

    Args:
        files: Every file's rows, keyed by name.

    Returns:
        One message per problem.
    """
    known = set()
    for rows in files.values():
        for row in rows:
            known.add(row["id"])

    problems = []
    for name, rows in files.items():
        for row in rows:
            for cited in CITATION.findall(row.get("notes", "")):
                if cited not in known:
                    problems.append(f"{name}: {row['id']} cites {cited}, which is gone")
    return problems


def check_contamination(rows: list) -> list[str]:
    """Checks that no seed query appears verbatim in a prompt.

    Args:
        rows: The seed rows.

    Returns:
        One message per problem.
    """
    # Every prompt as text
    prompts = {}
    for path in sorted(PROMPTS_DIR.glob("*.md")):
        prompts[path.name] = path.read_text(encoding="utf-8")

    problems = []
    for row in rows:
        query = row.get("query", "")
        if not query:
            continue

        # Which prompts hold this query
        naming = []
        for name, text in prompts.items():
            if query in text:
                naming.append(name)

        if naming:
            where = ", ".join(naming)
            problems.append(f"seed: {row['id']} appears verbatim in {where}")
    return problems


def check_database(places: list, retrieval: list) -> list[str]:
    """Checks that every expected id exists, and that ids listed together are one place.

    Args:
        places: The places rows.
        retrieval: The retrieval rows.

    Returns:
        One message per problem, or a note when the database is unreachable.
    """
    # Every id to look up, skipping the address and street labels
    place_ids = []
    for row in places:
        for place_id in row.get("expected", []):
            if NAMESPACED.match(place_id):
                place_ids.append(place_id)

    chunk_ids = []
    for row in retrieval:
        chunk_ids.extend(row.get("expected", []))

    try:
        connection = connect()
    except psycopg.OperationalError as error:
        # No database
        return [f"skipped: the database is unreachable ({error.__class__.__name__})"]

    # A live database that rejects a query
    try:
        with connection, connection.cursor() as cursor:
            # Every place id in one query, keeping the coordinates and the kind
            cursor.execute(
                "SELECT id, lat, lon, kind FROM places WHERE id = ANY(%s);",
                (place_ids,),
            )
            found = {}
            for place_id, lat, lon, kind in cursor.fetchall():
                found[place_id] = (lat, lon, kind)

            # Every chunk id in one query
            cursor.execute("SELECT id FROM chunks WHERE id = ANY(%s);", (chunk_ids,))
            chunks = set()
            for (chunk_id,) in cursor.fetchall():
                chunks.add(chunk_id)
    except psycopg.Error as error:
        return [f"the database rejected a query: {error.__class__.__name__}: {error}"]

    # Every id has to exist
    problems = []
    for row in places:
        for place_id in row.get("expected", []):
            if NAMESPACED.match(place_id) and place_id not in found:
                problems.append(
                    f"places: {row['id']} {place_id} is not in the database"
                )

    for row in retrieval:
        for chunk_id in row.get("expected", []):
            if chunk_id not in chunks:
                problems.append(f"retrieval: {row['id']} {chunk_id} is not a chunk")

    # Rows listing more than one id
    for row in places:
        located = []
        for place_id in row.get("expected", []):
            if place_id in found:
                located.append((place_id, found[place_id]))

        # Measure every pair
        for index, (first_id, first) in enumerate(located):
            first_lat, first_lon, first_kind = first
            for second_id, second in located[index + 1 :]:
                second_lat, second_lon, second_kind = second
                meters = (
                    distance_km(first_lat, first_lon, (second_lat, second_lon)) * 1000
                )

                # Areas get the wider limit
                both_areas = first_kind in AREA_KINDS and second_kind in AREA_KINDS
                limit = SAME_AREA_METERS if both_areas else SAME_PLACE_METERS
                if meters > limit:
                    problems.append(
                        f"places: {row['id']} accepts {first_id} and {second_id}, "
                        f"{meters:.0f} m apart"
                    )
    return problems


def report_shares(rows: list) -> None:
    """Prints how far each domain and style sits from its target share.

    Args:
        rows: The seed rows.
    """
    # Count the rows in each domain and style
    total = len(rows)
    domains = Counter(row.get("domain") for row in rows)
    styles = Counter(row.get("style") for row in rows)

    # The two typo styles share one target
    styles["typo+abbrev"] = styles["typo"] + styles["abbrev"]

    # Compare each count against its target
    drifted = []
    for name, share in list(DOMAIN_TARGETS.items()) + list(STYLE_TARGETS.items()):
        counts = domains if name in DOMAIN_TARGETS else styles
        target = share * total
        if abs(counts[name] - target) > SHARE_SLACK * total:
            drifted.append(f"{name} {counts[name]} against {target:.1f}")

    if drifted:
        print(f"  shares off target: {', '.join(drifted)}")
    else:
        print("  shares on target")


def main() -> int:
    """Runs every check and prints the result.

    Returns:
        The process exit code: 1 when anything failed.
    """
    seed = load("seed")
    places = load("places")
    retrieval = load("retrieval")
    files = {"seed": seed, "places": places, "retrieval": retrieval}
    templates = load_templates()

    print(
        f"Validating {len(seed)} seed, {len(places)} places, "
        f"{len(retrieval)} retrieval rows"
    )
    if not templates:
        print("  note: prompts/refusal.md is missing, so refusal wording is unchecked")

    shape = check_shape("seed", seed, "q", SEED_FIELDS)
    shape += check_shape("places", places, "p", PLACES_FIELDS)
    shape += check_shape("retrieval", retrieval, "r", RETRIEVAL_FIELDS)

    checks = [
        ("shape", shape),
        ("seed values and coherence", check_seed(seed, templates)),
        ("places expectations", check_places(places)),
        ("retrieval expectations", check_retrieval(retrieval)),
        ("prose", check_prose(files)),
        ("cross-references", check_citations(files)),
        ("prompt contamination", check_contamination(seed)),
        ("database", check_database(places, retrieval)),
    ]

    failed = 0
    for name, problems in checks:
        skipped = len(problems) == 1 and problems[0].startswith("skipped:")
        if not problems:
            print(f"  ok    {name}")
            continue
        if skipped:
            print(f"  --    {name}: {problems[0]}")
            continue
        failed += len(problems)
        print(f"  FAIL  {name}")
        for problem in problems:
            print(f"          {problem}")

    report_shares(seed)

    print()
    if failed:
        print(f"{failed} problems")
        return 1
    print("No problems")
    return 0


if __name__ == "__main__":
    sys.exit(main())
