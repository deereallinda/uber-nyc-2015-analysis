# app.py
# Streamlit Uber NYC 2015 Analysis App
# Author: Linda Mthembu

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
# I am always resolving the data path relative to this file,
# so the app works no matter where Streamlit is launched from.
APP_ROOT = Path(__file__).parent
DATA_PATH = APP_ROOT / "data" / "uber-raw-data.csv"

# I am keeping a list of possible datetime column names I can work with.
DATETIME_CANDIDATES = ["Date/Time", "DateTime", "Pickup_date", "Pickup_Date"]

st.set_page_config(
    page_title="Uber NYC 2015 – Data Analysis",
    page_icon="🚕",
    layout="wide",
)

# -------------------------------------------------------------------
# GLOBAL STYLING (CSS)
# -------------------------------------------------------------------
# I am injecting a bit of custom CSS to make the app feel more like a
# polished analytics dashboard.
st.markdown(
    """
    <style>
        /* Global font + background tweaks */
        html, body, [class*="stApp"] {
            font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: radial-gradient(circle at 0 0, #101820 0, #050608 35%, #02040a 70%, #000000 100%);
            color: #E5EDF5;
        }

        /* Main container */
        .main, .block-container {
            padding-top: 1.8rem;
            padding-bottom: 1.8rem;
        }

        /* Page title */
        h1 {
            font-weight: 800 !important;
            letter-spacing: 0.03em;
        }

        /* Section subheaders */
        h2, h3 {
            font-weight: 700 !important;
        }

        /* KPI cards */
        .metric-card {
            padding: 1.0rem 1.2rem;
            border-radius: 0.9rem;
            border: 1px solid rgba(255, 255, 255, 0.06);
            background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
            box-shadow: 0 14px 30px rgba(0, 0, 0, 0.40);
        }
        .metric-label {
            font-size: 0.80rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #9CA3AF;
        }
        .metric-value {
            font-size: 1.6rem;
            font-weight: 700;
            margin-top: 0.25rem;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background: radial-gradient(circle at top left, #111827 0, #020617 50%, #000000 100%);
            border-right: 1px solid rgba(148,163,184,0.25);
        }
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3 {
            color: #E5EDF5 !important;
        }

        /* Tabs */
        button[role="tab"] {
            padding: 0.45rem 1.2rem;
            border-radius: 999px !important;
        }
        button[role="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #4ade80, #22c55e) !important;
            color: #020617 !important;
            font-weight: 700 !important;
        }

        /* Footer */
        .footer {
            margin-top: 2.5rem;
            padding-top: 1.2rem;
            border-top: 1px solid rgba(148,163,184,0.35);
            font-size: 0.9rem;
            color: #9CA3AF;
        }
        .footer a {
            color: #e5edf5;
            text-decoration: none;
            margin-right: 1rem;
        }
        .footer a:hover {
            color: #4ade80;
        }
        .social-icon {
            vertical-align: middle;
            margin-right: 0.30rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# LOAD DATA
# -------------------------------------------------------------------
@st.cache_data(show_spinner="Loading trip data…")
def load_data() -> Tuple[pd.DataFrame, str]:
    """I am loading the sample CSV and returning (dataframe, datetime_column_name)."""

    # 1. Basic file checks
    if not DATA_PATH.exists():
        st.error(
            f"Data file **{DATA_PATH}** was not found.\n\n"
            "I need you to re-run the Jupyter notebook cell that exports "
            "`uber-raw-data.csv` and then refresh this app."
        )
        st.stop()

    if DATA_PATH.stat().st_size == 0:
        st.error(
            f"**{DATA_PATH}** exists but is empty.\n\n"
            "I need a non-empty sample exported to `data/uber-raw-data.csv` "
            "before I can continue."
        )
        st.stop()

    df = pd.read_csv(DATA_PATH)

    # 2. I am trying to find a usable datetime column
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
            "I could not find a usable date/time column.\n\n"
            f"Columns available: {df.columns.tolist()}"
        )
        st.stop()

    # 3. I am parsing and engineering common time features
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

st.markdown(
    """
I built this dashboard to explore how **Uber demand** behaves across **time of day**,  
**day of week**, and **dispatch bases** in New York City using a sampled 2015 dataset.

On the left, I let you control the **date range** and **hour filters**.  
Use the tabs below to move between different views of the data.
"""
)

st.markdown("---")

# -------------------------------------------------------------------
# SIDEBAR – FILTERS
# -------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Filters")

    with st.expander("Columns in dataset", expanded=False):
        st.write(sorted(list(df.columns)))

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
# KPI SUMMARY CARDS
# -------------------------------------------------------------------
k_col1, k_col2, k_col3 = st.columns(3)

total_trips = len(filtered)
unique_days = filtered["date"].nunique()
bases = filtered["Base"].nunique() if "Base" in filtered.columns else 0

with k_col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Total trips (filtered)</div>
            <div class="metric-value">{total_trips:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k_col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Unique service days</div>
            <div class="metric-value">{unique_days:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k_col3:
    bases_display = bases if bases else "N/A"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Active dispatch bases</div>
            <div class="metric-value">{bases_display}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")

# -------------------------------------------------------------------
# TABBED LAYOUT FOR CHARTS
# -------------------------------------------------------------------
tab_hour, tab_weekday, tab_base = st.tabs(
    ["⏰ Hourly demand", "📅 Day-of-week profile", "🏢 Dispatch base activity"]
)

# -------------------------------------------------------------------
# 1. TRIPS BY HOUR OF DAY
# -------------------------------------------------------------------
with tab_hour:
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
        color_discrete_sequence=["#22c55e"],
    )
    fig_hour.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_hour, use_container_width=True)

    # I am generating automated insights for the hourly profile
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
        - Morning commute hours (07:00–09:00) contribute about **{morning_share:.1%}** of all filtered trips,
          while evening commute hours (16:00–19:00) contribute **{evening_share:.1%}**.
        - Together, these windows capture a large share of demand, reflecting classic **home ↔ work travel patterns**.
        """
    )

# -------------------------------------------------------------------
# 2. TRIPS BY DAY OF WEEK
# -------------------------------------------------------------------
with tab_weekday:
    st.subheader("Demand by Day of Week")

    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

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
        color_discrete_sequence=["#38bdf8"],
    )
    fig_weekday.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_weekday, use_container_width=True)

    # I am generating automated insights for weekday profile
    valid_weekdays = weekday_counts.dropna(subset=["trips"])
    peak_day_row = valid_weekdays.loc[valid_weekdays["trips"].idxmax()]
    off_day_row = valid_weekdays.loc[valid_weekdays["trips"].idxmin()]

    peak_day = peak_day_row["weekday"]
    peak_day_trips = int(peak_day_row["trips"])
    off_day = off_day_row["weekday"]
    off_day_trips = int(off_day_row["trips"])

    weekday_mask = valid_weekdays["weekday"].isin(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    )
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
        - This confirms that **weekday commute behaviour** dominates the overall trip volume,
          while weekends reflect a more leisure-driven but still meaningful demand.
        """
    )

# -------------------------------------------------------------------
# 3. BASE ACTIVITY (OPTIONAL, if Base column exists)
# -------------------------------------------------------------------
with tab_base:
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
            color_discrete_sequence=["#f97316"],
        )
        fig_base.update_layout(margin=dict(l=10, r=10, t=40, b=10))
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
              of all base-level activity.
            - This concentration suggests opportunities to **rebalance fleet supply**
              or replicate high-performing base practices at lower-volume locations.
            """
        )
    else:
        st.info("This dataset does not contain a `Base` column, so base activity cannot be visualised.")

# -------------------------------------------------------------------
# FOOTER WITH SOCIAL ICONS
# -------------------------------------------------------------------
st.markdown(
    """
    <div class="footer">
        <div>
            Built by <strong>Linda Mthembu</strong> — Data Analyst &amp; Junior Data Engineer<br/>
            This dashboard is powered by a sampled Uber NYC 2015 dataset saved to
            <code>data/uber-raw-data.csv</code>.
        </div>
        <br/>
        <div>
            <a href="https://www.linkedin.com/in/linda-mthembu-66b877270/" target="_blank">
                <span class="social-icon">🔗</span>LinkedIn
            </a>
            <a href="https://github.com/deereallinda" target="_blank">
                <span class="social-icon">🐙</span>GitHub
            </a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
