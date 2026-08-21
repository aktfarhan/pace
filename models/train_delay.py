"""Train the delay model on the prepared LAMP arrivals."""

from datetime import date, timedelta
from itertools import pairwise
from pathlib import Path

import joblib
import numpy
import pandas
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score

ROOT = Path(__file__).resolve().parent.parent
IN_FILE = ROOT / "data" / "raw" / "lamp_delays.parquet"
OUT_FILE = ROOT / "models" / "artifacts" / "delay.pkl"

# The last four weeks are held out and never trained on
HELD_OUT_DAYS = 28

# A train counts as late past this many minutes
LATE_MINUTES = 5

# The window a line's recent lateness is read over
WINDOW_SECONDS = 900

# How many arrivals to fit on
SAMPLE = 2_000_000

# What the model reads
FEATURES = ["recent", "stop_rate", "route_id"]

# Where low ends and high begins
CUTOFFS = (0.2, 0.5)

# How many buckets the calibration error is measured over
BINS = 10


def recent_lateness(frame: pandas.DataFrame) -> pandas.Series:
    """Reads how late a line was running just before each arrival.

    Args:
        frame: Prepared arrivals, sorted by line and scheduled time.

    Returns:
        The share of those arrivals that ran late, or NaN where the
        window holds nothing.
    """
    window = frame["scheduled_arrival_time"] // WINDOW_SECONDS
    line = ["service_date", "route_id"]

    # Every arrival in the window before this one
    counted = frame.groupby(line + [window])["late"]
    keys = frame.set_index(line + [window]).index
    late = keys.map(counted.sum().groupby(level=[0, 1]).shift(1)).astype("float64")
    seen = keys.map(counted.size().groupby(level=[0, 1]).shift(1)).astype("float64")

    # Less whatever this same trip put into it
    own = frame.groupby(line + ["trip_id", window])["late"].agg(["sum", "size"])
    own = own.groupby(level=[0, 1, 2]).shift(1)
    mine = frame.set_index(line + ["trip_id", window]).index
    late -= mine.map(own["sum"]).astype("float64").fillna(0)
    seen -= mine.map(own["size"]).astype("float64").fillna(0)

    return pandas.Series(
        numpy.where(seen > 0, late / seen, numpy.nan), index=frame.index
    )


def calibration_error(truth: numpy.ndarray, chance: numpy.ndarray) -> float:
    """Measures how far the stated chances sit from what happened.

    Args:
        truth: Whether each arrival was late.
        chance: The chance the model gave it.

    Returns:
        The expected calibration error.
    """
    edges = numpy.linspace(0, 1, BINS + 1)
    error = 0.0

    # Each bucket's gap between promise and outcome, weighted by its size
    for low, high in pairwise(edges):
        inside = (chance > low) & (chance <= high)
        if inside.sum():
            error += inside.mean() * abs(truth[inside].mean() - chance[inside].mean())

    return error


print(f"Training on {IN_FILE}")
arrivals = pandas.read_parquet(
    IN_FILE,
    columns=[
        "service_date",
        "route_id",
        "trip_id",
        "stop_id",
        "scheduled_arrival_time",
        "delay_minutes",
    ],
)
arrivals["late"] = (arrivals["delay_minutes"] > LATE_MINUTES).astype("int8")
arrivals = arrivals.sort_values(["service_date", "route_id", "scheduled_arrival_time"])
arrivals["recent"] = recent_lateness(arrivals)
arrivals["route_id"] = arrivals["route_id"].astype("category")

# The split runs on time
last = date.fromisoformat(str(arrivals["service_date"].max()))
cutoff = int((last - timedelta(days=HELD_OUT_DAYS - 1)).strftime("%Y%m%d"))
earlier = arrivals[arrivals["service_date"] < cutoff]
held_out = arrivals[arrivals["service_date"] >= cutoff].copy()

print(f"  train {len(earlier):,} arrivals before {cutoff}")
print(
    f"  test  {len(held_out):,} arrivals from {cutoff} to {arrivals['service_date'].max()}"
)

# A stop's own record, read only from the training window
stop_rate = earlier.groupby("stop_id")["late"].mean()
prior = float(earlier["late"].mean())

# What each side is fitted and judged on
fitting = earlier.sample(n=min(SAMPLE, len(earlier)), random_state=0).copy()
fitting["stop_rate"] = fitting["stop_id"].map(stop_rate).fillna(prior)
held_out["stop_rate"] = held_out["stop_id"].map(stop_rate).fillna(prior)
fitting = fitting.dropna(subset=FEATURES)
held_out = held_out.dropna(subset=FEATURES)

model = HistGradientBoostingClassifier(
    max_iter=250,
    learning_rate=0.07,
    categorical_features=["route_id"],
    random_state=0,
)
print(f"  fitting on {len(fitting):,} of them")
model.fit(fitting[FEATURES], fitting["late"])

# Scored on the weeks the model never saw
chance = model.predict_proba(held_out[FEATURES])[:, 1]
truth = held_out["late"].to_numpy()
scores = {
    "auc": float(roc_auc_score(truth, chance)),
    "brier": float(brier_score_loss(truth, chance)),
    "ece": float(calibration_error(truth, chance)),
}
print(f"\nHeld out {len(held_out):,} arrivals")
print(
    f"  AUC {scores['auc']:.4f}   Brier {scores['brier']:.4f}   ECE {scores['ece']:.4f}"
)

# The three words a user reads
low, high = CUTOFFS
labels = pandas.cut(chance, [-0.01, low, high, 1.0], labels=["low", "mid", "high"])
print("\n  label  share   actually late")
for name, group in held_out.groupby(labels, observed=True):
    print(
        f"  {name:<6} {len(group) / len(held_out):>5.1%}   {group['late'].mean():>10.1%}"
    )

# Everything serving needs to repeat a prediction
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
half_written = OUT_FILE.with_suffix(".part.pkl")
joblib.dump(
    {
        "model": model,
        "stop_rate": stop_rate.to_dict(),
        "prior": prior,
        "features": FEATURES,
        "cutoffs": CUTOFFS,
        "late_minutes": LATE_MINUTES,
        "window_seconds": WINDOW_SECONDS,
        "routes": list(arrivals["route_id"].cat.categories),
        "held_out_from": int(cutoff),
        "scores": scores,
    },
    half_written,
)

# An interrupted dump must not land under the name serving reads
half_written.replace(OUT_FILE)
print(f"\nSaved {OUT_FILE} ({OUT_FILE.stat().st_size / 1e6:.1f} MB)")
