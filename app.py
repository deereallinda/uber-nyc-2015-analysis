# app.py
# Streamlit Uber NYC 2015 Analysis App
# Author: Linda Mthembu

from pathlib import Path
from typing import Tuple

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
# Always resolve the data path relative to this file,
# so it works even if you run Streamlit from another folder.
APP_ROOT = Path(__file__).parent
DATA_PATH = APP_ROOT / "data" / "uber-raw-data.csv"

# Candidate datetime column names we can recognise
DATETIME_CANDIDATES = ["Date/Time", "DateTime", "Pickup_date", "Pickup_Date"]

st.set_page_config(
    page_title="Uber NYC 2015 – Data Analysis",
    page_icon="🚕",
    layout="wide",
)

# -------------------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------------------
@st.cache_data(show_spinner="Loading trip data…")
def load_data() -> Tuple[pd.DataFrame, str]:
    """Load the sample CSV and return (dataframe, datetime_column_name)."""

    # 1. Basic file checks
    if not DATA_PATH.exists():
        st.error(
            f"Data file **{DATA_PATH}** was not found.\n\n"
            "Re-run the Jupyter notebook cell that exports "
            "`uber-raw-data.csv` and then refresh this app."
        )
        st.stop()

    if DATA_PATH.stat().st_size == 0:
        st.error(
            f"**{DATA_PATH}** exists but is empty.\n\n"
            "Regenerate the file from your notebook (export a sample to "
            "`data/uber-raw-data.csv`) and refresh the app."
        )
        st.stop()

    df = pd.read_csv(DATA_PATH)

    # 2. Find a usable datetime column
    date_col = None
    for c in DATETIME_CANDIDATES:
        if c in df.columns:
            date_col = c
            break

    # Fallback: build from DATE + TIME if they both exist
    if date_col is None and {"DATE", "TIME"}.issubset(df.columns):
        dt_str = df["DATE"].astype(str) + " " + df["TIME"].astype(str)
        date_col = "DateTime"
        df[date_col] = pd.to_datetime(dt_str, errors="coerce")

    if date_col is None:
        st.error(
            "Could not find a usable date/time column. "
            f"Columns available: {df.columns.tolist()}"
        )
        st.stop()

    # 3. Parse and engineer common time features
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    df["date"] = df[date_col].dt.date
    df["hour"] = df[date_col].dt.hour
    df["weekday"] = df[date_col].dt.day_name()

    # Normalise Base column if needed
    if "Base" not in df.columns and "Base Number" in df.columns:
        df = df.rename(columns={"Base Number": "Base"})

    return df, date_col


df, DATE_COL = load_data()

# -------------------------------------------------------------------
# PAGE HEADER
# -------------------------------------------------------------------
st.title("🚕 Uber NYC 2015 – Interactive Data Explorer")

st.write(
    """
    This dashboard presents an exploratory analysis of Uber trip data in New York City.
    Use the filters on the left to slice the data by date range and hour of day, and
    review the automated insights beneath each chart.
    """
)

# -------------------------------------------------------------------
# SIDEBAR – FILTERS
# -------------------------------------------------------------------
with st.sidebar:
    st.header("Filters")

    # Show available columns (for transparency / debugging)
    with st.expander("Show columns in dataset"):
        st.write(list(df.columns))

    valid_dates = df[DATE_COL].dt.date
    min_date = valid_dates.min()
    max_date = valid_dates.max()

    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    date_mask = df[DATE_COL].dt.date.between(start_date, end_date)

    hour_range = st.slider("Hour of day", 0, 23, (0, 23))
    h_min, h_max = hour_range

    filtered = df.loc[date_mask].copy()
    filtered = filtered[(filtered["hour"] >= h_min) & (filtered["hour"] <= h_max)]

    st.markdown("---")
    st.write(f"Rows after filtering: **{len(filtered):,}**")

if filtered.empty:
    st.warning("No trips match the current filter selection. Try widening the filters.")
    st.stop()

# -------------------------------------------------------------------
# KPI SUMMARY
# -------------------------------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Trips (filtered)", f"{len(filtered):,}")
with col2:
    st.metric("Unique Days", filtered["date"].nunique())
with col3:
    bases = filtered["Base"].nunique() if "Base" in filtered.columns else "N/A"
    st.metric("Unique Bases", bases)

st.markdown("---")

# -------------------------------------------------------------------
# 1. TRIPS BY HOUR OF DAY
# -------------------------------------------------------------------
st.subheader("Hourly Demand Profile")

hour_counts = (
    filtered.groupby("hour")
    .size()
    .reset_index(name="trips")
    .sort_values("hour")
)

fig_hour = px.bar(
    hour_counts,
    x="hour",
    y="trips",
    labels={"hour": "Hour of day", "trips": "Number of trips"},
)
st.plotly_chart(fig_hour, use_container_width=True)

# Automated insights for hourly profile
peak_hour_row = hour_counts.loc[hour_counts["trips"].idxmax()]
off_hour_row = hour_counts.loc[hour_counts["trips"].idxmin()]

peak_hour = int(peak_hour_row["hour"])
peak_trips = int(peak_hour_row["trips"])
off_hour = int(off_hour_row["hour"])
off_trips = int(off_hour_row["trips"])

morning_mask = hour_counts["hour"].between(7, 9)
evening_mask = hour_counts["hour"].between(16, 19)
morning_share = hour_counts.loc[morning_mask, "trips"].sum() / hour_counts["trips"].sum()
evening_share = hour_counts.loc[evening_mask, "trips"].sum() / hour_counts["trips"].sum()

st.markdown(
    f"""
**Insights – Hourly Demand**

- Peak activity occurs around **{peak_hour:02d}:00**, with approximately **{peak_trips:,} trips** in the filtered data.
- The quietest period is around **{off_hour:02d}:00**, with only **{off_trips:,} trips**.
- Morning commute hours (07:00–09:00) account for about **{morning_share:.1%}** of all filtered trips,
  while evening commute hours (16:00–19:00) contribute **{evening_share:.1%}**.
- Together, these commute windows capture the majority of demand, confirming classic
  **home ↔ work travel patterns**.
"""
)

st.markdown("---")

# -------------------------------------------------------------------
# 2. TRIPS BY DAY OF WEEK
# -------------------------------------------------------------------
st.subheader("Demand by Day of Week")

weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

weekday_counts = (
    filtered.groupby("weekday")
    .size()
    .reindex(weekday_order)
    .reset_index(name="trips")
)

fig_weekday = px.bar(
    weekday_counts,
    x="weekday",
    y="trips",
    labels={"weekday": "Day of week", "trips": "Number of trips"},
)
st.plotly_chart(fig_weekday, use_container_width=True)

# Automated insights for weekday profile
valid_weekdays = weekday_counts.dropna(subset=["trips"])
peak_day_row = valid_weekdays.loc[valid_weekdays["trips"].idxmax()]
off_day_row = valid_weekdays.loc[valid_weekdays["trips"].idxmin()]

peak_day = peak_day_row["weekday"]
peak_day_trips = int(peak_day_row["trips"])
off_day = off_day_row["weekday"]
off_day_trips = int(off_day_row["trips"])

weekday_mask = valid_weekdays["weekday"].isin(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
weekend_mask = valid_weekdays["weekday"].isin(["Saturday", "Sunday"])

weekday_avg = valid_weekdays.loc[weekday_mask, "trips"].mean()
weekend_avg = valid_weekdays.loc[weekend_mask, "trips"].mean()

st.markdown(
    f"""
**Insights – Weekday vs Weekend**

- The busiest day in the filtered period is **{peak_day}** with roughly **{peak_day_trips:,} trips**.
- The quietest day is **{off_day}**, with around **{off_day_trips:,} trips**.
- Average weekday demand is **{weekday_avg:,.0f} trips per day**, compared to
  **{weekend_avg:,.0f} trips per day** on weekends.
- This suggests that **weekday commute patterns** dominate overall demand,
  with weekends showing a more leisure-driven but still substantial volume.
"""
)

st.markdown("---")

# -------------------------------------------------------------------
# 3. BASE ACTIVITY (OPTIONAL, if Base column exists)
# -------------------------------------------------------------------
if "Base" in filtered.columns:
    st.subheader("Dispatch Base Activity")

    base_counts = (
        filtered.groupby("Base")
        .size()
        .reset_index(name="trips")
        .sort_values("trips", ascending=False)
    )

    fig_base = px.bar(
        base_counts.head(15),
        x="Base",
        y="trips",
        labels={"Base": "Dispatch base", "trips": "Number of trips"},
    )
    st.plotly_chart(fig_base, use_container_width=True)

    top_base_row = base_counts.iloc[0]
    top_base = top_base_row["Base"]
    top_base_trips = int(top_base_row["trips"])
    share_top_base = top_base_trips / base_counts["trips"].sum()

    st.markdown(
        f"""
**Insights – Fleet / Base Utilisation**

- The most active dispatch base in the filtered slice is **{top_base}** with
  approximately **{top_base_trips:,} trips**, accounting for **{share_top_base:.1%}**
  of all activity.
- Concentration of volume in a few bases suggests opportunities to
  **rebalance fleet supply** or **extend high-performing base practices**
  to lower-volume locations.
"""
    )

st.markdown(
    """
---
*Built by **Linda Mthembu – Data Analyst & Project Manager***  
_This dashboard is powered by a sampled dataset saved to `data/uber-raw-data.csv`._
"""
)
