"""Village 2 cafeteria waste advisor: streamlit vendor dashboard.

PROTOTYPE: all results are SIMULATED (see docs/assumptions.md).

Run from the project root:  streamlit run app.py
"""

from datetime import date, timedelta
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from src.advisor import MODEL_PATH, advise, load_model

HISTORY_PATH = Path(__file__).resolve().parent / "data" / "cafeteria_days.csv"
# Status colours for the risk tiers (always shown with a text legend, never colour alone).
RISK_COLOURS = {"low": "#0ca30c", "medium": "#fab219", "high": "#d03b3b"}

st.set_page_config(page_title="Village 2 Waste Advisor", page_icon="🍱")

# Visible on every run, above everything else. Blue so it never looks like a risk alert.
st.info(
    icon="🧪",
    body=
    "**SIMULATED RESULTS — prototype only.** The model is trained on simulated days "
    "built from a 56-student survey, not real sales. Do not use for real decisions.",
)

st.title("Village 2 cafeteria waste advisor")
st.caption("Pick tomorrow's conditions to get a waste-risk estimate and lunch batch advice.")


@st.cache_resource
def get_model(modified_time):
    # modified_time is only here so the cache reloads after `python src/train.py`.
    return load_model()


model = get_model(MODEL_PATH.stat().st_mtime)


@st.cache_data
def get_history(modified_time):
    # Reloads after `python src/simulate.py`, like the model above.
    return pd.read_csv(HISTORY_PATH, parse_dates=["date"])

# --- Inputs ----------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    day = st.date_input("Date", value=date.today() + timedelta(days=1))  # tomorrow
    calendar = st.selectbox(
        "Calendar", ["normal", "exam", "holiday", "break"],
        format_func=lambda c: {"normal": "Normal teaching day", "exam": "Exam week",
                               "holiday": "Public holiday", "break": "Semester break"}[c],
    )
with col2:
    weather = st.selectbox("Weather", ["clear", "rainy", "hazy"], format_func=str.capitalize)
    # A11: no classes on holidays and breaks, so lock class load to light
    # (this matches how the model was trained).
    no_classes = calendar in ("holiday", "break")
    class_load = st.selectbox(
        "Class load", ["light", "normal", "heavy"],
        index=0 if no_classes else 1,
        format_func=str.capitalize,
        disabled=no_classes,
        key=f"class_load_{no_classes}",  # new key so the default resets when this changes
        help="Set to Light on holidays and breaks, since there are no classes." if no_classes else None,
    )

result = advise(model, day, calendar, weather, class_load)

st.divider()
st.subheader(f"{result['day_of_week']}, {day:%d %B %Y}")

# --- Risk tier -------------------------------------------------------------------
risk = result["risk"]
message = (f"**{risk.upper()} waste risk** "
           f"(model confidence {result['confidence']:.0%}, simulated)")
{"low": st.success, "medium": st.warning, "high": st.error}[risk](message)

# --- Footfall and batch --------------------------------------------------------
m1, m2 = st.columns(2)
m1.metric(
    "Estimated lunch footfall",
    f"{result['footfall']} diners",
    delta=f"{result['vs_normal']:+.0%} vs normal day (400)",
    delta_color="normal" if result["vs_normal"] else "off",
    delta_arrow="auto" if result["vs_normal"] else "off",  # no "↑" on a 0% change
)
batch_change = result["suggested_batch"] - result["usual_batch"]
m2.metric(
    "Suggested batch",
    f"{result['suggested_batch']} meals",
    delta=f"{batch_change:+d} vs usual {result['usual_batch']}",
    delta_color="inverse" if batch_change else "off",  # cooking less shows green
    delta_arrow="auto" if batch_change else "off",
)

if batch_change < 0:
    st.write(f"🍲 **Batch advice:** cook about **{-batch_change} fewer** meals than usual.")
elif batch_change > 0:
    st.write(f"🍲 **Batch advice:** cook about **{batch_change} more** meals than usual "
             "so you don't run out.")
else:
    st.write("🍲 **Batch advice:** keep your usual batch.")

# --- Energy tip ------------------------------------------------------------------
st.write(f"⚡ **Off-peak energy tip:** {result['tip']}")

# --- Past days -----------------------------------------------------------------------
st.divider()
st.subheader("Past days (simulated)")

history = get_history(HISTORY_PATH.stat().st_mtime).copy()
history["similar"] = (history["calendar"] == calendar) & (history["weather"] == weather)
similar = history[history["similar"]]

label = f"{calendar} days with {weather} weather"
if len(similar):
    st.write(
        f"**{len(similar)}** past {label}: on average **{similar['footfall'].mean():.0f} diners**, "
        f"and **{(similar['waste_risk'] == 'high').mean():.0%}** were high waste risk. "
        "They are highlighted below."
    )
else:
    st.write(f"No past {label} in the simulated history.")

base = alt.Chart(history).encode(
    x=alt.X("date:T", title=None, axis=alt.Axis(format="%b", grid=False)),
    y=alt.Y("footfall:Q", title="Lunch diners", scale=alt.Scale(domainMin=0)),
)
line = base.mark_line(strokeWidth=1.5, color="#b4b2a9")
points = base.mark_circle(size=60, stroke="#ffffff", strokeWidth=1).encode(
    color=alt.Color(
        "waste_risk:N", title="Waste risk",
        scale=alt.Scale(domain=list(RISK_COLOURS), range=list(RISK_COLOURS.values())),
        legend=alt.Legend(orient="top"),
    ),
    opacity=alt.condition("datum.similar", alt.value(1.0), alt.value(0.25)),
    tooltip=[
        alt.Tooltip("date:T", format="%a %d %b %Y", title="Date"),
        alt.Tooltip("calendar:N", title="Calendar"),
        alt.Tooltip("weather:N", title="Weather"),
        alt.Tooltip("class_load:N", title="Class load"),
        alt.Tooltip("footfall:Q", title="Diners"),
        alt.Tooltip("waste_risk:N", title="Waste risk"),
    ],
)
batch_line = alt.Chart(pd.DataFrame({"y": [400]})).mark_rule(
    strokeDash=[4, 4], color="#5f5e58").encode(y="y:Q")
st.altair_chart((line + batch_line + points).properties(height=320),
                use_container_width=True)
st.caption("Each dot is one simulated day. The dashed line is the usual batch of 400 meals; "
           "dots below it mean cooked food was left over. Hover a dot for details.")

with st.expander("Show past days as a table"):
    st.dataframe(
        history.loc[history["similar"] if len(similar) else history.index,
                    ["date", "day_of_week", "calendar", "weather", "class_load",
                     "footfall", "surplus", "waste_risk"]],
        hide_index=True, use_container_width=True,
        column_config={"date": st.column_config.DateColumn("date", format="D MMM YYYY")},
    )

with st.expander("How is this worked out?"):
    st.markdown(
        "- **Risk tier:** a decision tree (max depth 4) trained on 250 simulated days. "
        "See `docs/tree.png`.\n"
        "- **Footfall:** 400 × survey-based multipliers for day, calendar, weather and "
        "class load (A6, A19).\n"
        "- **Batch:** footfall + 10% buffer, rounded up to 10, and not above 400 unless "
        "more diners are expected (A20).\n"
        "- **Energy tip:** 60% of lunch diners arrive by 1 pm according to the survey (A21).\n"
        "- The risk tier (from the tree) and the footfall (from the formula) can differ by one "
        "level on days close to a threshold.\n\n"
        "All assumption IDs are explained in `docs/assumptions.md`."
    )

st.caption("SIMULATED RESULTS — TEB2023 AI group project prototype.")
