"""Village 2 cafeteria waste advisor: streamlit vendor dashboard.

PROTOTYPE: all results are SIMULATED (see docs/assumptions.md).

Run from the project root:  streamlit run app.py
"""

from datetime import date, timedelta

import streamlit as st

from src.advisor import MODEL_PATH, advise, load_model

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
