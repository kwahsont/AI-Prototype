"""Village 2 cafeteria waste advisor: streamlit vendor dashboard.

PROTOTYPE: all results are SIMULATED (see docs/assumptions.md).

Run from the project root:  streamlit run app.py
The pages live in views/; this file adds the banner and the page menu.
"""

import streamlit as st

st.set_page_config(page_title="Village 2 Waste Advisor", page_icon="🍱")

# Visible on every page, above everything else. Blue so it never looks like a risk alert.
st.info(
    icon="🧪",
    body="**SIMULATED RESULTS — prototype only.** The model is trained on simulated days "
         "built from a 56-student survey, not real sales. Do not use for real decisions.",
)

page = st.navigation([
    st.Page("views/advisor.py", title="Advisor", icon="🍱", default=True),
    st.Page("views/week.py", title="Week planner", icon="📅"),
])
page.run()

st.caption("SIMULATED RESULTS — TEB2023 AI group project prototype.")
