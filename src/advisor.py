"""Shared advice logic for the dashboard (app.py) and the scenario script.

PROTOTYPE: the advice is based on a model trained on SIMULATED data.
Multipliers are imported from src/simulate.py so there is only one copy of
each number. Assumption IDs refer to docs/assumptions.md.
"""

import math
from datetime import date
from pathlib import Path

import joblib
import pandas as pd

from src.simulate import (
    BASE_FOOTFALL, BATCH_SIZE, CALENDAR_MULT, CLASS_LOAD_MULT, DAY_MULT, WEATHER_MULT,
)

MODEL_PATH = Path(__file__).resolve().parent.parent / "model.pkl"

BATCH_BUFFER = 0.10      # A20
ROUND_TO = 10            # A20
FIRST_ROUND_SHARE = 0.60  # A21: diners who arrive by 1 pm


def load_model():
    return joblib.load(MODEL_PATH)


def expected_multiplier(day_of_week, calendar, weather, class_load):
    """Combined footfall multiplier (A6): the individual ones multiply."""
    return (CALENDAR_MULT[calendar]
            * WEATHER_MULT[weather]
            * DAY_MULT.get(day_of_week, 1.00)
            * CLASS_LOAD_MULT[class_load])


def suggested_batch(footfall):
    """A20: footfall + 10% buffer, rounded up to 10, but no more than the usual
    batch unless more diners than usual are expected."""
    buffered = round(footfall * (1 + BATCH_BUFFER), 6)  # round() avoids 440.0000001 -> 450
    batch = math.ceil(buffered / ROUND_TO) * ROUND_TO
    return batch if footfall > BATCH_SIZE else min(batch, BATCH_SIZE)


def energy_tip(risk, batch):
    """Two-round cooking tip based on the lunch timing in the survey (A21)."""
    first = math.ceil(batch * FIRST_ROUND_SHARE / ROUND_TO) * ROUND_TO
    second = batch - first
    tip = (f"Cook about {first} meals before noon for the 12–1 pm rush, and the other "
           f"{second} around 1:15 pm for later diners, so food isn't kept hot all afternoon.")
    if risk == "high":
        tip += " Today is high risk: only cook the second round if the first sells out."
    return tip


QUESTION_WORDING = {
    "day_of_week": "Is it a {}?",
    "calendar": {"normal": "Is it a normal teaching day?", "exam": "Is it exam week?",
                 "holiday": "Is it a public holiday?", "break": "Is it a semester break?"},
    "weather": "Is the weather {}?",
    "class_load": "Is the class load {}?",
}


def explain(model, inputs: pd.DataFrame):
    """The questions the tree asked for one day, in order, plus what the final
    leaf contains. Used for the dashboard's "Why this risk?" panel."""
    encode, tree = model.named_steps["encode"], model.named_steps["tree"]
    x = encode.transform(inputs)
    x = x.toarray() if hasattr(x, "toarray") else x
    names = [n.split("__", 1)[1] for n in encode.get_feature_names_out()]

    steps = []
    for node in tree.decision_path(x).indices:
        feature_index = tree.tree_.feature[node]
        if feature_index < 0:  # leaf: no question asked here
            continue
        name = names[feature_index]                       # e.g. "weather_rainy"
        group = next(g for g in QUESTION_WORDING if name.startswith(g + "_"))
        value = name[len(group) + 1:]                     # e.g. "rainy"
        wording = QUESTION_WORDING[group]
        question = wording[value] if isinstance(wording, dict) else wording.format(value)
        steps.append((question, "Yes" if x[0, feature_index] > 0.5 else "No"))

    leaf = tree.apply(x)[0]
    n_days = int(tree.tree_.n_node_samples[leaf])
    values = tree.tree_.value[leaf][0]
    # Newer scikit-learn stores shares (summing to 1) instead of day counts.
    counts = values * n_days if values.sum() <= 1.0 + 1e-9 else values
    leaf_counts = {c: int(round(v)) for c, v in zip(tree.classes_, counts)}
    return steps, n_days, leaf_counts


def advise(model, day: date, calendar, weather, class_load):
    """Return everything the dashboard shows for one day."""
    day_of_week = day.strftime("%A")
    inputs = pd.DataFrame([{
        "day_of_week": day_of_week, "calendar": calendar,
        "weather": weather, "class_load": class_load,
    }])
    risk = model.predict(inputs)[0]
    probs = dict(zip(model.classes_, model.predict_proba(inputs)[0]))

    multiplier = expected_multiplier(day_of_week, calendar, weather, class_load)
    footfall = round(BASE_FOOTFALL * multiplier)                                # A19
    batch = suggested_batch(footfall)                                           # A20

    return {
        "date": day.isoformat(),
        "day_of_week": day_of_week,
        "calendar": calendar,
        "weather": weather,
        "class_load": class_load,
        "risk": risk,
        "confidence": probs[risk],
        "footfall": footfall,
        "vs_normal": multiplier - 1,
        "usual_batch": BATCH_SIZE,
        "suggested_batch": batch,
        "tip": energy_tip(risk, batch),
    }
