"""Log a day page: the vendor records what really happened, then retrains.

This is how simulated data gets replaced by real data over time.
Logged days are saved to data/vendor_log.csv (no personal data).
"""

from datetime import date, datetime

import pandas as pd
import streamlit as st

from src.simulate import HIGH_FROM, MEDIUM_FROM
from src.train import VENDOR_LOG, train_and_evaluate
from views.shared import WEATHERS, calendar_select, class_load_select

LOG_COLUMNS = ["date", "day_of_week", "calendar", "weather", "class_load",
               "batch_size", "leftovers", "surplus_share", "waste_risk", "logged_at"]


def risk_from_leftovers(cooked, leftovers):
    """Same thresholds as the simulation (A18), so logged and simulated days match."""
    share = leftovers / cooked
    if share < MEDIUM_FROM:
        return share, "low"
    if share < HIGH_FROM:
        return share, "medium"
    return share, "high"


def read_log():
    if VENDOR_LOG.exists():
        return pd.read_csv(VENDOR_LOG)
    return pd.DataFrame(columns=LOG_COLUMNS)


st.title("Log a day")
st.caption("Record what really happened at lunch. Logged days are added to the training "
           "data, so the model slowly learns from real days instead of simulated ones.")

# --- Entry form ----------------------------------------------------------------------
c1, c2 = st.columns(2)
with c1:
    day = st.date_input("Date", value=date.today(), max_value=date.today())
    calendar = calendar_select(key="log_calendar")
with c2:
    weather = st.selectbox("Weather", WEATHERS, format_func=str.capitalize, key="log_weather")
    class_load = class_load_select(calendar, key_prefix="log_class_load")

with st.form("log_form", clear_on_submit=True):
    f1, f2 = st.columns(2)
    cooked = f1.number_input("Meals cooked for lunch", min_value=1, max_value=2000, value=400, step=10)
    leftovers = f2.number_input("Meals left over", min_value=0, max_value=2000, value=0, step=5)
    submitted = st.form_submit_button("Save this day", type="primary")

if submitted:
    if leftovers > cooked:
        st.error("Leftovers can't be more than meals cooked.")
    else:
        share, risk = risk_from_leftovers(cooked, leftovers)
        log = read_log()
        log = log[log["date"] != day.isoformat()]  # one entry per date: re-logging replaces it
        entry = pd.DataFrame([{
            "date": day.isoformat(), "day_of_week": day.strftime("%A"),
            "calendar": calendar, "weather": weather, "class_load": class_load,
            "batch_size": cooked, "leftovers": leftovers,
            "surplus_share": round(share, 3), "waste_risk": risk,
            "logged_at": datetime.now().isoformat(timespec="seconds"),
        }])
        log = pd.concat([log, entry], ignore_index=True).sort_values("date")
        VENDOR_LOG.parent.mkdir(exist_ok=True)
        log.to_csv(VENDOR_LOG, index=False)
        st.success(f"Saved {day:%a %d %b}: {leftovers} of {cooked} left over "
                   f"({share:.0%}) → **{risk}** waste risk.")

# --- Logged days ---------------------------------------------------------------------
st.divider()
log = read_log()
st.subheader(f"Logged days ({len(log)})")
if len(log):
    st.dataframe(log.drop(columns="logged_at"), hide_index=True, use_container_width=True,
                 column_config={"surplus_share": st.column_config.NumberColumn(
                     "left over", format="percent")})
    st.download_button("Download log (CSV)", log.to_csv(index=False),
                       file_name="vendor_log.csv", mime="text/csv")
else:
    st.write("No days logged yet.")

# --- Retrain -------------------------------------------------------------------------
st.divider()
st.subheader("Retrain the model")
st.write(f"Training data now: **250 simulated days + {len(log)} logged "
         f"day{'' if len(log) == 1 else 's'}**. "
         "Each logged day counts the same as one simulated day, so you need many real "
         "days before they change the advice much.")
if st.button("Retrain with logged days", disabled=len(log) == 0):
    with st.spinner("Training…"):
        metrics = train_and_evaluate(verbose=False)
    tree_cv = next(r for name, r in metrics["comparison"].items() if "tree" in name.lower())
    st.success(f"Model retrained on {metrics['n_simulated']} simulated + "
               f"{metrics['n_logged']} logged days. Cross-validated accuracy: "
               f"{tree_cv['mean']:.2f}. The Advisor and Week planner now use the new model.")
