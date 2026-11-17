"""Train the waste-risk decision tree on the SIMULATED cafeteria days.

PROTOTYPE: the training data comes from src/simulate.py, not real records.

Run from the project root:  python src/train.py
Outputs: model.pkl, docs/tree.png, and metrics printed to the terminal.
"""

from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")  # save the plot to a file; no window needed
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier, plot_tree

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "cafeteria_days.csv"
MODEL_OUT = ROOT / "model.pkl"
TREE_OUT = ROOT / "docs" / "tree.png"

# Only the four inputs a vendor knows in advance. Footfall, surplus and
# multiplier are left out: they are how the label was made, so using them
# would let the model cheat.
FEATURES = ["day_of_week", "calendar", "weather", "class_load"]
TARGET = "waste_risk"
CLASSES = ["low", "medium", "high"]

SEED = 42
TEST_SHARE = 0.2
MAX_DEPTH = 4


def main():
    df = pd.read_csv(DATA)
    X, y = df[FEATURES], df[TARGET]

    # Stratify so train and test keep the same mix of low/medium/high.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SHARE, stratify=y, random_state=SEED
    )

    # The tree needs numbers, so each category becomes a 0/1 column
    # (e.g. weather_rainy). Keeping this inside the pipeline means
    # model.pkl accepts plain text inputs like "rainy".
    model = Pipeline([
        ("encode", ColumnTransformer([
            ("onehot", OneHotEncoder(handle_unknown="ignore"), FEATURES)
        ])),
        ("tree", DecisionTreeClassifier(max_depth=MAX_DEPTH, random_state=SEED)),
    ])
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    baseline = (y_test == y_train.mode()[0]).mean()  # always guess the most common class

    print(f"SIMULATED data: {len(X_train)} train days, {len(X_test)} test days\n")
    print(f"Test accuracy:      {accuracy_score(y_test, y_pred):.2f}")
    print(f"Baseline accuracy:  {baseline:.2f}  (always guessing '{y_train.mode()[0]}')\n")

    cm = confusion_matrix(y_test, y_pred, labels=CLASSES)
    print("Confusion matrix (rows = actual, columns = predicted):")
    print(pd.DataFrame(cm, index=CLASSES, columns=CLASSES).to_string())

    joblib.dump(model, MODEL_OUT)
    print(f"\nSaved model -> {MODEL_OUT}")

    # Clean up names like "onehot__weather_rainy" to "weather_rainy" for the plot.
    names = [n.split("__", 1)[1] for n in model.named_steps["encode"].get_feature_names_out()]
    tree = model.named_steps["tree"]
    fig, ax = plt.subplots(figsize=(22, 10))
    plot_tree(tree, feature_names=names, class_names=list(tree.classes_),
              filled=True, rounded=True, impurity=False, fontsize=9, ax=ax)
    ax.set_title(f"Waste-risk decision tree (max_depth {MAX_DEPTH}) — trained on SIMULATED data")
    # scikit-learn sorts classes alphabetically, so spell out the order for readers.
    fig.text(0.5, 0.01,
             f"value = day counts for [{', '.join(tree.classes_)}].  "
             "'weather_rainy <= 0.5' means 'not rainy' (True goes left).",
             ha="center", fontsize=11)
    TREE_OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(TREE_OUT, dpi=120, bbox_inches="tight")
    print(f"Saved tree plot -> {TREE_OUT}")


if __name__ == "__main__":
    main()
