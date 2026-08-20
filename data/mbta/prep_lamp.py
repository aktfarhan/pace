"""Turn the raw LAMP days into one table of arrival delays."""

from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas
import pyarrow
import pyarrow.parquet

ROOT = Path(__file__).resolve().parent.parent.parent
IN_DIR = ROOT / "data" / "raw" / "lamp"
OUT_FILE = ROOT / "data" / "raw" / "lamp_delays.parquet"
BOSTON = ZoneInfo("America/New_York")

# What the model reads
KEEP = [
    "service_date",
    "trip_id",
    "route_id",
    "branch_route_id",
    "trunk_route_id",
    "stop_id",
    "parent_station",
    "stop_sequence",
    "direction_id",
    "scheduled_arrival_time",
    "scheduled_travel_time",
    "scheduled_headway_trunk",
    "scheduled_headway_branch",
    "headway_trunk_seconds",
    "headway_branch_seconds",
    "dwell_time_seconds",
    "travel_time_seconds",
    "hour",
    "weekday",
    "delay_minutes",
]


def delays_of(path: Path) -> pandas.DataFrame:
    """Reads one LAMP day and works out how late each arrival was.

    Args:
        path: One raw LAMP day file, named for its service date.

    Returns:
        The day's arrivals, one row per stop, with delay_minutes.
    """
    frame = pandas.read_parquet(path)
    frame = frame.dropna(subset=["stop_timestamp", "scheduled_arrival_time"])

    # Unscheduled service, joined to a schedule it never ran
    frame = frame[~frame["trip_id"].str.startswith("ADDED")]

    # The stop a trip waits at before it starts
    starts = frame.groupby("trip_id")["stop_sequence"].transform("min")
    frame = frame[frame["stop_sequence"] != starts]

    # Where the schedule's seconds are counted from
    day = date.fromisoformat(path.stem)
    noon = datetime(day.year, day.month, day.day, 12, tzinfo=BOSTON)
    anchor = noon.timestamp() - 12 * 3600

    scheduled = anchor + frame["scheduled_arrival_time"]
    frame["delay_minutes"] = (frame["stop_timestamp"] - scheduled) / 60

    # When the trip was due, as the model sees it
    frame["hour"] = (frame["scheduled_arrival_time"] // 3600).astype("int16")
    frame["weekday"] = noon.weekday()

    return frame[KEEP]


days = sorted(IN_DIR.glob("*.parquet"))
print(f"Preparing {len(days)} LAMP days -> {OUT_FILE}")

writer = None
kept = 0
blank = []
for number, path in enumerate(days, start=1):
    frame = delays_of(path)

    # LAMP publishes an empty file for a day it holds no data
    if frame.empty:
        blank.append(path.stem)
        continue
    kept += len(frame)

    # One row group per day
    table = pyarrow.Table.from_pandas(frame, preserve_index=False)
    if writer is None:
        writer = pyarrow.parquet.ParquetWriter(OUT_FILE, table.schema)
    writer.write_table(table)

    # Progress, every thirtieth day
    if number % 30 == 0 or number == len(days):
        print(f"  {number}/{len(days)} days, {kept:,} arrivals")

writer.close()

size = OUT_FILE.stat().st_size
print(f"Wrote {kept:,} arrivals to {OUT_FILE} ({size / 1e6:.0f} MB)")
if blank:
    print(f"{len(blank)} days held no data: {', '.join(blank)}")
