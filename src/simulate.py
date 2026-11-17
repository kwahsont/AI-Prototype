"""Build simulated cafeteria days for Village 2 cafeteria.

PROTOTYPE: every row is simulated, not observed. Each number below
points to an assumption ID in docs/assumptions.md.

Run from the project root:  python src/simulate.py
Output: data/cafeteria_days.csv
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42  # fixed so everyone gets the same CSV
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "cafeteria_days.csv"

# --- Footfall multipliers (1.00 = normal day) ---------------------------------
CALENDAR_MULT = {"normal": 1.00, "exam": 1.15, "holiday": 0.15, "break": 0.15}  # Step 3, A9
WEATHER_MULT = {"clear": 1.00, "rainy": 0.70, "hazy": 0.95}                      # Step 3
DAY_MULT = {"Friday": 1.05, "Saturday": 0.95, "Sunday": 0.95}                    # Step 3, A7 (others 1.00)
CLASS_LOAD_MULT = {"light": 1.10, "normal": 1.00, "heavy": 0.90}                 # A10

# --- Simulation settings --------------------------------------------------------
N_DAYS = 250                                   # A12
START = date(2026, 1, 5)                       # A12 (a Monday)
CYCLE = ["normal"] * 14 + ["exam"] * 2 + ["break"] * 3  # A12: weeks in one 19-week cycle
N_PUBLIC_HOLIDAYS = 15                         # A13
WEATHER_PROBS = {"clear": 0.55, "rainy": 0.35, "hazy": 0.10}       # A14
CLASS_LOAD_PROBS = {"light": 0.25, "normal": 0.50, "heavy": 0.25}  # A11
BASE_FOOTFALL = 400                            # A15
NOISE_SD = 0.10                                # A16
BATCH_SIZE = 400                               # A17
MEDIUM_FROM, HIGH_FROM = 0.10, 0.25            # A18


def build_calendar(rng):
    """One row per day with date, day_of_week and calendar type."""
    days = [START + timedelta(days=i) for i in range(N_DAYS)]
    calendar = [CYCLE[(i // 7) % len(CYCLE)] for i in range(N_DAYS)]

    # A13: turn a few teaching weekdays into public holidays.
    teaching_weekdays = [i for i, d in enumerate(days)
                         if calendar[i] == "normal" and d.weekday() < 5]
    for i in rng.choice(teaching_weekdays, N_PUBLIC_HOLIDAYS, replace=False):
        calendar[i] = "holiday"

    return pd.DataFrame({
        "date": days,
        "day_of_week": [d.strftime("%A") for d in days],
        "calendar": calendar,
    })


def add_conditions(df, rng):
    """Draw weather and class load for each day."""
    df["weather"] = rng.choice(list(WEATHER_PROBS), len(df), p=list(WEATHER_PROBS.values()))
    df["class_load"] = rng.choice(list(CLASS_LOAD_PROBS), len(df), p=list(CLASS_LOAD_PROBS.values()))
    df.loc[df["calendar"].isin(["holiday", "break"]), "class_load"] = "light"  # A11
    return df


def add_footfall_and_risk(df, rng):
    """Expected footfall from multipliers, add noise, then compare with the batch."""
    df["multiplier"] = (
        df["calendar"].map(CALENDAR_MULT)
        * df["weather"].map(WEATHER_MULT)
        * df["day_of_week"].map(DAY_MULT).fillna(1.00)
        * df["class_load"].map(CLASS_LOAD_MULT)
    ).round(3)  # A6: multipliers multiply

    noise = rng.normal(1.0, NOISE_SD, len(df))  # A16
    df["footfall"] = (BASE_FOOTFALL * df["multiplier"] * noise).clip(lower=0).round().astype(int)

    df["batch_size"] = BATCH_SIZE
    df["surplus"] = (df["batch_size"] - df["footfall"]).clip(lower=0)  # A18
    df["surplus_share"] = (df["surplus"] / df["batch_size"]).round(3)
    df["waste_risk"] = pd.cut(
        df["surplus_share"],
        bins=[-np.inf, MEDIUM_FROM, HIGH_FROM, np.inf],
        right=False,
        labels=["low", "medium", "high"],
    )
    return df


def main():
    rng = np.random.default_rng(SEED)
    df = build_calendar(rng)
    df = add_conditions(df, rng)
    df = add_footfall_and_risk(df, rng)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)

    print(f"SIMULATED data: {len(df)} days -> {OUTPUT}")
    print(df["waste_risk"].value_counts().reindex(["low", "medium", "high"]).to_string())


if __name__ == "__main__":
    main()
