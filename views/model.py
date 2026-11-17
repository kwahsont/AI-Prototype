"""Model page: how the decision tree was built and how well it does.

Reads the files written by `python src/train.py`, `python -m src.sensitivity`
and `python -m src.scenarios`, so it always shows the latest run.
"""

import json

import pandas as pd
import streamlit as st

from views.shared import ROOT

DOCS = ROOT / "docs"

st.title("How the model works")
st.caption("Everything on this page comes from SIMULATED data.")

metrics = json.loads((DOCS / "model_metrics.json").read_text())

# --- Summary -------------------------------------------------------------------------
tree_cv = next(r for name, r in metrics["comparison"].items() if "tree" in name.lower())
baseline_cv = next(r for name, r in metrics["comparison"].items() if "baseline" in name.lower())
c1, c2, c3 = st.columns(3)
c1.metric("Training days", f"{metrics['n_simulated'] + metrics['n_logged']}",
          help=f"{metrics['n_simulated']} simulated + {metrics['n_logged']} logged")
c2.metric("Tree accuracy (5-fold)", f"{tree_cv['mean']:.0%}")
c3.metric("Guessing baseline", f"{baseline_cv['mean']:.0%}",
          help="Always predicting the most common risk level")

st.markdown(
    "**In one sentence:** a decision tree learned from past days which conditions lead to "
    "low, medium or high leftover food, using four inputs the vendor knows in advance: "
    "day of week, calendar, weather and class load."
)

# --- The tree --------------------------------------------------------------------------
st.subheader("1. The decision tree")
st.write("Read it from the top. Each box asks a yes/no question; True goes left. "
         "The bottom boxes are the answers.")
st.image(str(DOCS / "tree.png"), use_container_width=True)
st.caption("Hover the image and click the ⤢ icon to see it full size. The same file is "
           "docs/tree.png. Each day's own path is shown on the Advisor page under "
           "'Why this risk?'.")

# --- Comparison ------------------------------------------------------------------------
st.subheader("2. Compared with other models")
comparison = pd.DataFrame(
    [{"Model": n, "Accuracy": r["mean"], "Spread (±)": r["sd"]}
     for n, r in metrics["comparison"].items()])
st.dataframe(comparison, hide_index=True, use_container_width=True,
             column_config={"Accuracy": st.column_config.NumberColumn(format="percent"),
                            "Spread (±)": st.column_config.NumberColumn(format="percent")})
st.caption("5-fold cross-validation: each model is tested 5 times on days it didn't train on. "
           "Logistic regression scores about the same, but the tree is kept because a "
           "vendor can follow its questions.")

# --- Mistakes and importance -------------------------------------------------------------
st.subheader("3. Where it goes wrong, and what it relies on")
left, right = st.columns(2)
with left:
    st.image(str(DOCS / "confusion_matrix.png"), use_container_width=True)
    recall = metrics["recall"]
    st.caption(f"On {metrics['n_test']} held-out days it caught {recall['low']:.0%} of low, "
               f"{recall['medium']:.0%} of medium and {recall['high']:.0%} of high days. "
               "Medium days are rare and sit between two thresholds, so the tree tends to "
               "call them low or high.")
with right:
    st.image(str(DOCS / "feature_importance.png"), use_container_width=True)
    top = [f.replace("_", " ") for f in metrics["importance"]]
    note = (f"{top[0].capitalize()} and {top[1]} matter most; {top[-1]} matters least.")
    if top[-1] == "day of week":
        note += (" Its Friday and weekend effects (about ±5%) are smaller than the "
                 "day-to-day noise, so the tree ignores it.")
    st.caption(note)

# --- Scenarios and sensitivity -----------------------------------------------------------
st.subheader("4. Test scenarios")
scenarios = DOCS / "scenarios.csv"
if scenarios.exists():
    st.dataframe(pd.read_csv(scenarios), hide_index=True, use_container_width=True)

st.subheader("5. How much do our guesses matter?")
sensitivity = DOCS / "sensitivity.md"
if sensitivity.exists():
    # Skip the file's own title line; the page already has a heading.
    st.markdown(sensitivity.read_text().split("\n", 1)[1])

st.info("These numbers show the tree can learn the patterns we built into the simulation "
        "(see docs/assumptions.md). They don't show real-world accuracy yet: that needs "
        "real days from the Log a day page.")
