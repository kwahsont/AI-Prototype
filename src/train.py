"""Train and evaluate the waste-risk decision tree.

PROTOTYPE: the training data comes from src/simulate.py, not real records.

Run from the project root:  python src/train.py
Outputs:
  model.pkl                       the decision tree the dashboard uses
  docs/tree.png                   the tree, readable as if/then questions
  docs/confusion_matrix.png       test-set mistakes by class
  docs/feature_importance.png     which inputs the tree relies on
  docs/model_report.md            all numbers below, as tables for the report
  docs/model_metrics.json         the same numbers for the dashboard's Model page
"""

import json
from pathlib import Path

import joblib
import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")  # save plots to files; no window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier, plot_tree

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "cafeteria_days.csv"
VENDOR_LOG = ROOT / "data" / "vendor_log.csv"   # real days logged in the dashboard
MODEL_OUT = ROOT / "model.pkl"
DOCS = ROOT / "docs"

# Only the four inputs a vendor knows in advance. Footfall, surplus and
# multiplier are left out: they are how the label was made, so using them
# would let the model cheat.
FEATURES = ["day_of_week", "calendar", "weather", "class_load"]
TARGET = "waste_risk"
CLASSES = ["low", "medium", "high"]

SEED = 42
TEST_SHARE = 0.2
CV_FOLDS = 5
MAX_DEPTH = 4
# Each leaf must hold at least 5 training days. Without this, some leaves were
# built from 1 day and showed "100% confidence" for a single random day.
MIN_SAMPLES_LEAF = 5


def encoder():
    # The models need numbers, so each category becomes a 0/1 column
    # (e.g. weather_rainy). Keeping this inside the pipeline means
    # model.pkl accepts plain text inputs like "rainy".
    return ColumnTransformer([("onehot", OneHotEncoder(handle_unknown="ignore"), FEATURES)])


def make_tree():
    return Pipeline([
        ("encode", encoder()),
        ("tree", DecisionTreeClassifier(max_depth=MAX_DEPTH, min_samples_leaf=MIN_SAMPLES_LEAF,
                                        random_state=SEED)),
    ])


def candidate_models():
    """Models compared in the report. Only the tree is used by the dashboard."""
    return {
        "Baseline (always most common class)": Pipeline([
            ("encode", encoder()), ("model", DummyClassifier(strategy="most_frequent"))]),
        "Logistic regression": Pipeline([
            ("encode", encoder()), ("model", LogisticRegression(max_iter=1000))]),
        f"Decision tree (depth {MAX_DEPTH}) — used": make_tree(),
    }


def load_training_data():
    """Simulated days, plus any real days the vendor has logged."""
    df = pd.read_csv(DATA)[FEATURES + [TARGET]].assign(source="simulated")
    if VENDOR_LOG.exists():
        log = pd.read_csv(VENDOR_LOG)
        if len(log):
            df = pd.concat([df, log[FEATURES + [TARGET]].assign(source="logged")],
                           ignore_index=True)
    return df


def readable_names(model):
    # "onehot__weather_rainy" -> "weather_rainy"
    return [n.split("__", 1)[1] for n in model.named_steps["encode"].get_feature_names_out()]


def grouped_importance(model):
    """Add up the one-hot columns so each of the 4 inputs gets one score."""
    names = readable_names(model)
    scores = model.named_steps["tree"].feature_importances_
    totals = {f: 0.0 for f in FEATURES}
    for name, score in zip(names, scores):
        feature = next(f for f in FEATURES if name.startswith(f + "_"))
        totals[feature] += score
    return dict(sorted(totals.items(), key=lambda kv: kv[1], reverse=True))


def compare_models(X, y):
    """5-fold cross-validation: every day is used for testing exactly once."""
    folds = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=SEED)
    results = {}
    for name, model in candidate_models().items():
        scores = cross_val_score(model, X, y, cv=folds, scoring="accuracy")
        results[name] = {"mean": float(scores.mean()), "sd": float(scores.std())}
    return results


def save_tree_plot(model, path):
    tree = model.named_steps["tree"]
    fig, ax = plt.subplots(figsize=(22, 10))
    plot_tree(tree, feature_names=readable_names(model), class_names=list(tree.classes_),
              filled=True, rounded=True, impurity=False, fontsize=9, ax=ax)
    ax.set_title(f"Waste-risk decision tree (max_depth {MAX_DEPTH}) — trained on SIMULATED data")
    # scikit-learn sorts classes alphabetically, so spell out the order for readers.
    fig.text(0.5, 0.01,
             f"value = day counts for [{', '.join(tree.classes_)}].  "
             "'weather_rainy <= 0.5' means 'not rainy' (True goes left).",
             ha="center", fontsize=11)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def save_confusion_plot(cm, path):
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(3), CLASSES)
    ax.set_yticks(range(3), CLASSES)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, cm[i, j], ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() / 2 else "#0b0b0b", fontsize=13)
    ax.set_title("Test-set confusion matrix (SIMULATED)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_importance_plot(importance, path):
    fig, ax = plt.subplots(figsize=(6, 2.8))
    names = list(importance)[::-1]
    values = [importance[n] for n in names]
    ax.barh(names, values, color="#2a78d6", height=0.55)
    for y, v in enumerate(values):
        ax.text(v + 0.01, y, f"{v:.0%}", va="center", fontsize=10)
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xlabel("Share of how much the tree's splits sort the days (importance)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Which inputs the tree relies on (SIMULATED)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_report(m):
    rows = "\n".join(f"| {name} | {r['mean']:.2f} | ± {r['sd']:.2f} |"
                     for name, r in m["comparison"].items())
    cm = m["confusion_matrix"]
    cm_rows = "\n".join(f"| **{c}** | " + " | ".join(str(v) for v in cm[i]) + " |"
                        for i, c in enumerate(CLASSES))
    recall = "\n".join(f"| {c} | {m['recall'][c]:.0%} |" for c in CLASSES)
    imp = "\n".join(f"| {f} | {v:.0%} |" for f, v in m["importance"].items())
    text = f"""# Model report (SIMULATED data)

Generated by `python src/train.py`. Training data: {m['n_simulated']} simulated days
and {m['n_logged']} logged days.

## 1. Model comparison ({CV_FOLDS}-fold cross-validation)

The data is split into {CV_FOLDS} parts. Each model is trained on 4 parts and tested on
the 5th, five times over, so every day is used for testing once. This is fairer than a
single split.

| Model | Mean accuracy | Spread (sd) |
|---|---|---|
{rows}

## 2. Held-out test set (the saved model)

`model.pkl` is trained on {m['n_train']} days and tested on {m['n_test']} days it never saw.

- Test accuracy: **{m['test_accuracy']:.2f}**

Confusion matrix (rows = actual, columns = predicted):

| | low | medium | high |
|---|---|---|---|
{cm_rows}

How many days of each class the model caught (recall):

| Class | Recall |
|---|---|
{recall}

## 3. Which inputs matter

How much each input helps the tree sort days into low/medium/high (feature
importance; adds up to 100%):

| Input | Importance |
|---|---|
{imp}

## Reading these results

- The model learns from simulated data, so the accuracy shows the tree can recover
  the patterns written into `docs/assumptions.md`. It says nothing about real-world accuracy yet.
- **Medium is the weak class.** Medium days sit between two thresholds, where the ±10%
  noise decides the label, and there are fewer of them, so the tree tends to call them
  low or high instead.
- If logistic regression scores about the same, we still prefer the tree: a vendor can
  follow its if/then questions (see `docs/tree.png`).
"""
    (DOCS / "model_report.md").write_text(text)


def train_and_evaluate(verbose=True):
    """Train the tree, compare models, save every output. Returns the metrics."""
    df = load_training_data()
    X, y = df[FEATURES], df[TARGET]

    # Stratify so train and test keep the same mix of low/medium/high.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SHARE, stratify=y, random_state=SEED)
    model = make_tree().fit(X_train, y_train)
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred, labels=CLASSES)

    metrics = {
        "n_simulated": int((df["source"] == "simulated").sum()),
        "n_logged": int((df["source"] == "logged").sum()),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "test_accuracy": float(accuracy_score(y_test, y_pred)),
        "confusion_matrix": cm.tolist(),
        "recall": dict(zip(CLASSES, recall_score(y_test, y_pred, labels=CLASSES,
                                                 average=None, zero_division=0).tolist())),
        "importance": grouped_importance(model),
        "comparison": compare_models(X, y),
    }

    DOCS.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_OUT)
    save_tree_plot(model, DOCS / "tree.png")
    save_confusion_plot(cm, DOCS / "confusion_matrix.png")
    save_importance_plot(metrics["importance"], DOCS / "feature_importance.png")
    write_report(metrics)
    (DOCS / "model_metrics.json").write_text(json.dumps(metrics, indent=2))

    if verbose:
        print(f"SIMULATED data: {metrics['n_simulated']} simulated + "
              f"{metrics['n_logged']} logged days\n")
        print(f"{CV_FOLDS}-fold cross-validation accuracy:")
        for name, r in metrics["comparison"].items():
            print(f"  {name:40} {r['mean']:.2f} ± {r['sd']:.2f}")
        print(f"\nHeld-out test accuracy (saved tree): {metrics['test_accuracy']:.2f}")
        print("Confusion matrix (rows = actual, columns = predicted):")
        print(pd.DataFrame(cm, index=CLASSES, columns=CLASSES).to_string())
        print("\nRecall:", {c: f"{v:.0%}" for c, v in metrics["recall"].items()})
        print("Importance:", {f: f"{v:.0%}" for f, v in metrics["importance"].items()})
        print(f"\nSaved model.pkl and docs/ (tree, confusion matrix, importance, report)")
    return metrics


if __name__ == "__main__":
    train_and_evaluate()
