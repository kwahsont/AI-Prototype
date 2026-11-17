"""Village 2 cafeteria waste advisor: streamlit vendor dashboard.

PROTOTYPE: all results are SIMULATED (see docs/assumptions.md).

Run from the project root:  streamlit run app.py
The pages live in views/; this file adds the banner and the page menu.
"""

import streamlit as st

st.set_page_config(page_title="Village 2 Waste Advisor", page_icon="🚀")

# Space look: colours and fonts are in .streamlit/config.toml; this adds the
# starfield and a glow on the title. Purely decorative.
st.markdown("""
<style>
.stApp {
  background-color: #05070d;
  background-image:
    radial-gradient(1px 1px at 20px 30px, #ffffffcc, transparent),
    radial-gradient(1px 1px at 120px 80px, #ffffff99, transparent),
    radial-gradient(1.5px 1.5px at 200px 160px, #ffffffdd, transparent),
    radial-gradient(1px 1px at 310px 40px, #ffffff88, transparent),
    radial-gradient(1px 1px at 400px 210px, #ffffffaa, transparent),
    radial-gradient(1.5px 1.5px at 480px 120px, #cfe3ffcc, transparent),
    radial-gradient(1px 1px at 90px 250px, #ffffff77, transparent),
    radial-gradient(ellipse 60% 40% at 85% 0%, #1b2a5a55, transparent),
    radial-gradient(ellipse 50% 35% at 0% 100%, #3a1b5a44, transparent);
  background-size: 520px 280px, 520px 280px, 520px 280px, 520px 280px, 520px 280px,
                   520px 280px, 520px 280px, 100% 100%, 100% 100%;
  background-attachment: fixed;
}
h1 {
  color: #ffd23f !important;
  letter-spacing: 0.06em;
  text-shadow: 0 0 12px #ffd23f66, 0 0 28px #ffd23f22;
}
h2, h3 { letter-spacing: 0.04em; }
[data-testid="stExpander"], [data-testid="stDataFrame"] {
  box-shadow: 0 0 0 1px #2a3550, 0 0 18px #4aa3ff14;
  border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# Visible on every page, above everything else. Blue so it never looks like a risk alert.
st.info(
    icon="🧪",
    body="**SIMULATED RESULTS — prototype only.** The model is trained on simulated days "
         "built from a 56-student survey, not real sales. Do not use for real decisions.",
)

page = st.navigation([
    st.Page("views/advisor.py", title="Advisor", icon="🚀", default=True),
    st.Page("views/week.py", title="Week planner", icon="🛰️"),
    st.Page("views/log.py", title="Log a day", icon="📡"),
    st.Page("views/model.py", title="Model", icon="🪐"),
])
page.run()

st.caption("SIMULATED RESULTS — TEB2023 AI group project prototype.")
