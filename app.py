# app.py
# Streamlit Uber NYC 2015 Analysis App
# Author: Linda Mthembu

from pathlib import Path

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# ---------- Config ----------
DATA_PATH = Path("data") / "uber-raw-data.csv"
DATE_COL = "DateTime"   # single canonical datetime column

st.set_page_config(
    page_title="Uber NYC 2015 – Data Analysis",
    page_icon="🚕",
    layout="wide",
)

st.title("🚕 Uber NYC 2015 – Interactive Data Explorer")
st.write(
    """
    This app showcases my end-to-end exploratory data analysis of Uber trip data
    in New York City (2014–2015). Use the controls in the sidebar to filter the
    data and explore demand patterns.
    """
)

# ---------- Load data ----------
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)

    # 1. Ensure we have a single datetime column
    if DATE_COL not in df.columns:
        if {"DATE", "TIME"}.issubset(df.columns):
            # build a datetime string and parse
            dt_str = df["DATE"].astype(str) + " " + df["TIME"].astype(str)
            df[DATE_COL] = pd.to_datetime(dt_str, errors="coerce")
        else:
            st.error(
                "Could not find a usable date/time column. "
                f"Columns available: {df.columns.tolist()}"
            )
            st.stop()
    else:
        df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")

    # drop rows where datetime is missing to avoid date vs float issues
    df = df.dropna(subset=[DATE_COL])

    # 2. Create features the app expects
    df["date"] = df[DATE_COL].dt.date
    df["hour"] = df[DATE_COL].dt.hour
    df["weekday"] = df[DATE_COL].dt.day_name()

    # 3. Normalise the base column name
    if "Base" not in df.columns and "Base Number" in df.columns:
        df = df.rename(columns={"Base Number": "Base"})

    # 4. Make sure Lat/Lon are numeric if present (for the map)
    for col in ["Lat", "Lon"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


df = load_data()

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")

# Date range – work with clean, non-null dates
valid_dates = df[DATE_COL].dt.date.dropna()
min_date = valid_dates.min()
max_date = valid_dates.max()

date_range = st.sidebar.date_input(
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

filtered = df.loc[date_mask].copy()

# Hour filter
hour_range = st.sidebar.slider("Hour of day", 0, 23, (0, 23))
h_min, h_max = hour_range
filtered = filtered[(filtered["hour"] >= h_min) & (filtered["hour"] <= h_max)]

st.sidebar.write(f"Rows after filtering: **{len(filtered):,}**")

# ---------- KPIs ----------
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Trips", f"{len(filtered):,}")
with col2:
    st.metric("Unique Days", filtered["date"].nunique())
with col3:
    if "Base" in filtered.columns:
        st.metric("Unique Bases", filtered["Base"].nunique())
    else:
        st.metric("Unique Bases", "N/A")

st.markdown("---")

# ---------- Trips by hour ----------
st.subheader("Trips by Hour of Day")
hour_counts = filtered.groupby("hour").size().reset_index(name="trips")
fig_hour = px.bar(hour_counts, x="hour", y="trips", labels={"trips": "Number of trips"})
st.plotly_chart(fig_hour, use_container_width=True)

# ---------- Trips by weekday ----------
st.subheader("Trips by Day of Week")
weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekday_counts = (
    filtered.groupby("weekday").size().reindex(weekday_order).reset_index(name="trips")
)
fig_weekday = px.bar(
    weekday_counts,
    x="weekday",
    y="trips",
    labels={"trips": "Number of trips"},
)
st.plotly_chart(fig_weekday, use_container_width=True)

# ---------- Map ----------
st.subheader("Pickup Locations (sample)")
if {"Lat", "Lon"}.issubset(filtered.columns):
    sample = filtered.dropna(subset=["Lat", "Lon"]).sample(
        min(5000, len(filtered)), random_state=42
    )
    fig_map = px.scatter_mapbox(
        sample,
        lat="Lat",
        lon="Lon",
        zoom=9,
        height=500,
        opacity=0.5,
    )
    fig_map.update_layout(
        mapbox_style="open-street-map",
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("No latitude/longitude columns found to plot the map.")

st.markdown(
    """
    ---
    **Built by Linda Mthembu – Data Analyst & Project Manager**  
    Explore the full notebook and code on my GitHub profile.
    """
)
