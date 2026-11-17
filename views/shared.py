"""Helpers shared by the dashboard pages."""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.advisor import MODEL_PATH, load_model

ROOT = Path(__file__).resolve().parent.parent
HISTORY_PATH = ROOT / "data" / "cafeteria_days.csv"

# Status colours for the risk tiers (always shown with a text label, never colour alone).
RISK_COLOURS = {"low": "#0ca30c", "medium": "#fab219", "high": "#d03b3b"}
RISK_ALERT = {"low": st.success, "medium": st.warning, "high": st.error}

CALENDAR_LABELS = {"normal": "Normal teaching day", "exam": "Exam week",
                   "holiday": "Public holiday", "break": "Semester break"}
CALENDARS = list(CALENDAR_LABELS)
WEATHERS = ["clear", "rainy", "hazy"]
CLASS_LOADS = ["light", "normal", "heavy"]
NO_CLASS_CALENDARS = ("holiday", "break")  # A11: class load is always light


@st.cache_resource
def _model(modified_time):
    # modified_time is only here so the cache reloads after retraining.
    return load_model()


def get_model():
    return _model(MODEL_PATH.stat().st_mtime)


@st.cache_data
def _history(modified_time):
    return pd.read_csv(HISTORY_PATH, parse_dates=["date"])


def get_history():
    # Reloads after `python src/simulate.py`, like the model above.
    return _history(HISTORY_PATH.stat().st_mtime).copy()


def calendar_select(label="Calendar", key=None):
    return st.selectbox(label, CALENDARS, format_func=CALENDAR_LABELS.get, key=key)


def class_load_select(calendar, key_prefix="class_load"):
    """Class load, locked to Light on holidays and breaks (A11)."""
    no_classes = calendar in NO_CLASS_CALENDARS
    return st.selectbox(
        "Class load", CLASS_LOADS,
        index=0 if no_classes else 1,
        format_func=str.capitalize,
        disabled=no_classes,
        key=f"{key_prefix}_{no_classes}",  # new key so the default resets when this changes
        help="Set to Light on holidays and breaks, since there are no classes." if no_classes else None,
    )
