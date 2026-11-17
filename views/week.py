"""Week planner page: plan the next 7 days' lunch batches in one table."""

from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from src.advisor import advise
from views.shared import (CALENDAR_LABELS, CALENDARS, CLASS_LOADS, NO_CLASS_CALENDARS,
                          RISK_COLOURS, WEATHERS, get_model)

RISK_ICON = {"low": "🟢 low", "medium": "🟡 medium", "high": "🔴 high"}

st.title("Week planner")
st.caption("Set the conditions for each day of the week to plan batches and shopping. "
           "Double-click a Calendar, Weather or Class load cell to change it.")

model = get_model()

today = date.today()
next_monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
start = st.date_input("Week starting", value=next_monday)
days = [start + timedelta(days=i) for i in range(7)]

# --- Editable conditions -----------------------------------------------------------
default = pd.DataFrame({
    "Date": days,
    "Day": [d.strftime("%A") for d in days],
    "Calendar": "normal",
    "Weather": "clear",
    "Class load": "normal",
})
plan = st.data_editor(
    default,
    key=f"week_{start}",  # a new week starts from the defaults again
    hide_index=True,
    use_container_width=True,
    disabled=["Date", "Day"],
    column_config={
        "Date": st.column_config.DateColumn(format="D MMM"),
        "Calendar": st.column_config.SelectboxColumn(options=CALENDARS, required=True,
                                                     help=", ".join(f"{k} = {v}" for k, v in CALENDAR_LABELS.items())),
        "Weather": st.column_config.SelectboxColumn(options=WEATHERS, required=True),
        "Class load": st.column_config.SelectboxColumn(options=CLASS_LOADS, required=True),
    },
)

# A11: no classes on holidays and breaks.
locked = plan["Calendar"].isin(NO_CLASS_CALENDARS) & (plan["Class load"] != "light")
if locked.any():
    st.info("Class load is treated as light on holidays and breaks (no classes).")
plan.loc[plan["Calendar"].isin(NO_CLASS_CALENDARS), "Class load"] = "light"

# --- Advice for each day ------------------------------------------------------------
rows = []
for _, r in plan.iterrows():
    a = advise(model, r["Date"], r["Calendar"], r["Weather"], r["Class load"])
    rows.append({
        "Day": f"{r['Day'][:3]} {r['Date']:%d %b}",
        "short": f"{r['Day'][:3]} {r['Date'].day}",  # chart label; fits on narrow screens
        "risk": a["risk"],
        "Waste risk": RISK_ICON[a["risk"]],
        "Est. diners": a["footfall"],
        "Suggested batch": a["suggested_batch"],
        "vs usual 400": a["suggested_batch"] - a["usual_batch"],
    })
advice = pd.DataFrame(rows)

st.subheader("This week's advice (simulated)")
total = advice["Suggested batch"].sum()
usual = 400 * len(advice)
c1, c2, c3 = st.columns(3)
c1.metric("Meals to cook this week", f"{total:,}")
c2.metric("Usual week", f"{usual:,}")
c3.metric("Difference", f"{total - usual:+,}",
          delta_color="off")
high_days = advice.loc[advice["risk"] == "high", "Day"].tolist()
if high_days:
    st.write(f"🔴 **High waste risk:** {', '.join(high_days)}. Cook in two rounds on these days.")

st.dataframe(advice.drop(columns=["risk", "short"]), hide_index=True, use_container_width=True,
             column_config={"vs usual 400": st.column_config.NumberColumn(format="%+d")})

bars = alt.Chart(advice).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, width=28).encode(
    x=alt.X("short:N", sort=None, title=None, axis=alt.Axis(labelAngle=0, labelOverlap=False)),
    y=alt.Y("Suggested batch:Q", title="Meals", scale=alt.Scale(domainMin=0)),
    color=alt.Color("risk:N", title="Waste risk",
                    scale=alt.Scale(domain=list(RISK_COLOURS), range=list(RISK_COLOURS.values())),
                    legend=alt.Legend(orient="top")),
    tooltip=["Day", "Waste risk", "Est. diners", "Suggested batch"],
)
usual_line = alt.Chart(pd.DataFrame({"y": [400]})).mark_rule(
    strokeDash=[4, 4], color="#ffd23f").encode(y="y:Q")
st.altair_chart((bars + usual_line).properties(height=260), use_container_width=True)
st.caption("Bars are the suggested batch for each day; the dashed gold line is the usual 400.")
