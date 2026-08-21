"""Label how likely a planned trip is to run late."""

from datetime import datetime
from functools import lru_cache
from pathlib import Path

import joblib
import pandas

from backend.lateness import lateness
from backend.retrieve import Row

ROOT = Path(__file__).resolve().parent.parent
ARTIFACT = ROOT / "models" / "artifacts" / "delay.pkl"

# How far ahead a reading is worth using
REACH_SECONDS = 2700

# The branches that share a track
FAMILY = "Green-"


@lru_cache(maxsize=1)
def _load(saved_at: float) -> dict | None:
    """Reads the artifact from disk.

    Args:
        saved_at: When it was written.

    Returns:
        The saved bundle, or None where it cannot be read.
    """
    try:
        return joblib.load(ARTIFACT)
    except Exception as error:
        print(f"risk: {ARTIFACT.name} unreadable, {error}")
        return None


def trained() -> dict | None:
    """Loads the model and everything predicting with it needs.

    Returns:
        The saved bundle, or None.
    """
    try:
        return _load(ARTIFACT.stat().st_mtime)
    except OSError:
        return None


def warm() -> None:
    """Runs one throwaway prediction so the first question waits on none."""
    bundle = trained()
    if bundle is not None:
        chances(bundle, [{"route_id": bundle["routes"][0], "board_stop": ""}], [0.0])


def rides(chunks: list[Row]) -> list[dict]:
    """Picks the ride legs out of a planned trip.

    Args:
        chunks: The rows the answer was grounded in.

    Returns:
        Each ride's metadata, in travel order.
    """
    legs = []
    for _, kind, _, metadata, _ in chunks:
        if kind == "plan" and "route_id" in metadata:
            legs.append(metadata)
    return legs


def chances(bundle: dict, legs: list[dict], readings: list[float]) -> list[float]:
    """Asks the model how likely each ride is to run late.

    Args:
        bundle: The loaded model and its lookups.
        legs: The rides.
        readings: How late each ride's line is running now.

    Returns:
        One chance per ride.
    """
    stop_rate = bundle["stop_rate"]
    prior = bundle["prior"]

    # One row per ride
    rows = {
        "recent": readings,
        "stop_rate": [stop_rate.get(leg["board_stop"], prior) for leg in legs],
        "route_id": pandas.Categorical(
            [leg["route_id"] for leg in legs], categories=bundle["routes"]
        ),
    }

    # Columns in trained order
    frame = pandas.DataFrame(rows)
    return bundle["model"].predict_proba(frame[bundle["features"]])[:, 1].tolist()


def combined(legs: list[dict], per_ride: list[float]) -> float:
    """Folds a trip's rides into one chance of arriving late.

    Args:
        legs: The rides.
        per_ride: Each ride's chance of running late.

    Returns:
        The chance that any part of the trip runs late.
    """
    # Keep the worst chance on each line
    worst = {}
    for leg, value in zip(legs, per_ride, strict=True):
        route_id = leg["route_id"]
        family = FAMILY if route_id.startswith(FAMILY) else route_id
        worst[family] = max(worst.get(family, 0.0), value)

    # Multiply out every line running on time
    survives = 1.0
    for value in worst.values():
        survives *= 1.0 - value

    return 1.0 - survives


def label_for(chunks: list[Row], now: datetime) -> str | None:
    """Reads how risky a planned trip is.

    Args:
        chunks: The rows the answer was grounded in.
        now: The local time the question was asked.

    Returns:
        "low", "mid" or "high", or None.
    """
    legs = rides(chunks)
    if not legs:
        return None

    bundle = trained()
    if bundle is None:
        return None

    # Gather how late each leg's line is running now
    readings = []
    for leg in legs:
        if leg["route_id"] not in bundle["routes"]:
            return None

        # A reading this old has stopped predicting
        away = (datetime.fromisoformat(leg["depart"]) - now).total_seconds()
        if away > REACH_SECONDS:
            return None

        # A missing reading would read as a calm line
        reading = lateness(leg["route_id"])
        if reading is None:
            return None

        readings.append(reading)

    # Turn the trip's chance into the word a user sees
    low, high = bundle["cutoffs"]
    chance = combined(legs, chances(bundle, legs, readings))
    if chance <= low:
        return "low"
    if chance <= high:
        return "mid"
    return "high"
