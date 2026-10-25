"""Train the question parser on generated questions and save it."""

import time
from pathlib import Path

import joblib
import numpy
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, make_union

from backend.assistant.parse import bus_names, neighbor_features, token_features
from backend.mbta.stations import station_words
from backend.planner.timetable import gtfs_stamp
from models.parser_questions import check, generate

ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT / "models" / "artifacts" / "parser.pkl"

# Each fold's first-pass labels come from a model that never saw it
FOLDS = 4

# How closely the tagger and the text models fit
TAGGER_C = 5.0
TEXT_C = 10.0

# Features weaker than this are dropped
PRUNE = 0.05


def tagger():
    """Builds an untrained word tagger."""
    return make_pipeline(
        DictVectorizer(), LogisticRegression(max_iter=3000, C=TAGGER_C)
    )


def text_model(vocabularies=(None, None)):
    """Builds an untrained whole-question model."""
    words = TfidfVectorizer(
        ngram_range=(1, 2), sublinear_tf=True, vocabulary=vocabularies[0]
    )
    letters = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        sublinear_tf=True,
        vocabulary=vocabularies[1],
    )
    return make_pipeline(
        make_union(words, letters), LogisticRegression(max_iter=3000, C=TEXT_C)
    )


def prune_tagger(model) -> str:
    """Drops a tagger's weak features in place.

    Args:
        model: A trained tagger.

    Returns:
        How many features were kept.
    """
    vectorizer, classifier = model.steps[0][1], model.steps[1][1]
    keep = numpy.abs(classifier.coef_).max(axis=0) > PRUNE
    vectorizer.restrict(keep)
    classifier.coef_ = classifier.coef_[:, keep]
    classifier.n_features_in_ = int(keep.sum())
    return f"{keep.sum():,} of {len(keep):,}"


def prune_text(model, texts: list[str], labels: list[str]):
    """Retrains a whole-question model on its strong features only.

    Args:
        model: A trained text model.
        texts: The questions it was trained on.
        labels: Their answers.

    Returns:
        Tuple of (the smaller model, how many features were kept).
    """
    union, classifier = model.steps[0][1], model.steps[1][1]
    keep = numpy.abs(classifier.coef_).max(axis=0) > PRUNE
    vocabularies = []
    start = 0
    for _, vectorizer in union.transformer_list:
        terms = sorted(vectorizer.vocabulary_, key=vectorizer.vocabulary_.get)
        vocabularies.append([term for term, kept in zip(terms, keep[start:]) if kept])
        start += len(terms)
    return text_model(vocabularies).fit(
        texts, labels
    ), f"{keep.sum():,} of {len(keep):,}"


started = time.time()
rows = check(generate())
stations = station_words(gtfs_stamp())
buses = bus_names(gtfs_stamp())
features = [
    [
        token_features(row["words"], at, stations, buses)
        for at in range(len(row["words"]))
    ]
    for row in rows
]
tags = [row["tags"] for row in rows]

# First pass, each fold labelled by a model trained on the others
print(f"\nTraining on {len(rows):,} questions")
guesses = [None] * len(rows)
for fold in range(FOLDS):
    rest = [i for i in range(len(rows)) if i % FOLDS != fold]
    model = tagger().fit(
        [f for i in rest for f in features[i]], [t for i in rest for t in tags[i]]
    )
    for i in range(fold, len(rows), FOLDS):
        guesses[i] = list(model.predict(features[i]))
first = tagger().fit(
    [f for row in features for f in row], [t for row in tags for t in row]
)
print(
    f"  first pass, {time.time() - started:.0f}s, kept {prune_tagger(first)} features"
)

# Second pass, which also sees the first pass's labels nearby
second = tagger().fit(
    [
        features[i][at] | neighbor_features(guesses[i], at)
        for i in range(len(rows))
        for at in range(len(tags[i]))
    ],
    [t for row in tags for t in row],
)
print(f"  tagger, {time.time() - started:.0f}s, kept {prune_tagger(second)} features")

# Intent, and which schedule question it is
texts = [" ".join(row["words"]) for row in rows]
models = {"first_pass": first, "tagger": second}
for name in ("intent", "kind"):
    labels = [row["want"][name] for row in rows]
    models[name], kept = prune_text(text_model().fit(texts, labels), texts, labels)
    print(f"  {name}, {time.time() - started:.0f}s, kept {kept} features")

# Half-size weights; the answers don't change
for model in models.values():
    classifier = model.steps[-1][1]
    classifier.coef_ = classifier.coef_.astype(numpy.float32)
    classifier.intercept_ = classifier.intercept_.astype(numpy.float32)

# An interrupted dump must not land under the name serving reads
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
half_written = OUT_FILE.with_suffix(".part.pkl")
joblib.dump(models | {"trained_on": len(rows)}, half_written, compress=3)
half_written.replace(OUT_FILE)
print(f"\nSaved {OUT_FILE} ({OUT_FILE.stat().st_size / 1e6:.1f} MB)")
