"""Advisor page: one day's waste risk, batch advice and the reasoning behind it."""

from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from src.advisor import advise, explain
from views.shared import (RISK_ALERT, RISK_COLOURS, WEATHERS, calendar_select,
                          class_load_select, get_history, get_model)

st.title("Village 2 cafeteria waste advisor")
st.caption("Pick tomorrow's conditions to get a waste-risk estimate and lunch batch advice.")

model = get_model()

# --- Inputs ----------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    day = st.date_input("Date", value=date.today() + timedelta(days=1))  # tomorrow
    calendar = calendar_select()
with col2:
    weather = st.selectbox("Weather", WEATHERS, format_func=str.capitalize)
    class_load = class_load_select(calendar)

result = advise(model, day, calendar, weather, class_load)

st.divider()
st.subheader(f"{result['day_of_week']}, {day:%d %B %Y}")

# --- Risk tier -------------------------------------------------------------------
risk = result["risk"]
RISK_ALERT[risk](f"**{risk.upper()} waste risk** "
                 f"(model confidence {result['confidence']:.0%}, simulated)")

# --- Why this risk? --------------------------------------------------------------
inputs = pd.DataFrame([{"day_of_week": result["day_of_week"], "calendar": calendar,
                        "weather": weather, "class_load": class_load}])
steps, n_days, leaf_counts = explain(model, inputs)
with st.expander("Why this risk? Follow the decision tree", expanded=True):
    for i, (question, answer) in enumerate(steps, start=1):
        st.markdown(f"{i}. {question} → **{answer}**")
    st.markdown(
        f"**→ {risk.upper()}.** Of the **{n_days}** training days that ended up here, "
        f"{leaf_counts.get('low', 0)} were low, {leaf_counts.get('medium', 0)} medium and "
        f"{leaf_counts.get('high', 0)} high risk. That share is the confidence above."
    )
    st.caption("Questions the tree never asks for this kind of day don't affect the answer. "
               "The full tree is on the Model page.")

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

history = get_history()
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
line = base.mark_line(strokeWidth=1.5, color="#5c6b8a")
points = base.mark_circle(size=60, stroke="#05070d", strokeWidth=1).encode(
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
    strokeDash=[4, 4], color="#ffd23f").encode(y="y:Q")
st.altair_chart((line + batch_line + points).properties(height=320),
                use_container_width=True)
st.caption("Each dot is one simulated day. The dashed gold line is the usual batch of 400 meals; "
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
        "See the Model page.\n"
        "- **Footfall:** 400 × survey-based multipliers for day, calendar, weather and "
        "class load (A6, A19).\n"
        "- **Batch:** footfall + 10% buffer, rounded up to 10, and not above 400 unless "
        "more diners are expected (A20).\n"
        "- **Energy tip:** 60% of lunch diners arrive by 1 pm according to the survey (A21).\n"
        "- The risk tier (from the tree) and the footfall (from the formula) can differ by one "
        "level on days close to a threshold.\n\n"
        "All assumption IDs are explained in `docs/assumptions.md`."
    )
