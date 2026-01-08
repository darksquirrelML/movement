#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz

# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="Pick-up Lorry Availability",
    page_icon="🚐",
    layout="wide"
)

st.title("🚐 Pick-up Lorry Availability & Whereabout")

# -------------------------
# Timezone (Singapore)
# -------------------------
SG_TZ = pytz.timezone("Asia/Singapore")
now_dt = datetime.now(SG_TZ)
now_time = now_dt.time()

st.caption(f"🕒 Current Time (SG): **{now_dt.strftime('%H:%M')}**")

# -------------------------
# Database helpers
# -------------------------
DB_PATH = "data/pickup.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def load_data():
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM pickup_schedule", conn)
    conn.close()
    return df

def save_data(df):
    conn = get_conn()
    df.to_sql("pickup_schedule", conn, if_exists="replace", index=False)
    conn.close()

# -------------------------
# Load data
# -------------------------
df = load_data()

# Convert times
df["time_start_dt"] = pd.to_datetime(df["time_start"], errors="coerce").dt.time
df["time_end_dt"] = pd.to_datetime(df["time_end"], errors="coerce").dt.time

# -------------------------
# DRIVER WHEREABOUT UPDATE (AUTO-FILL)
# -------------------------
st.subheader("📍 Driver Whereabout Update (Auto-Save)")

vehicle = st.selectbox("Vehicle", df["vehicle_id"].unique())

active_row = df[
    (df["vehicle_id"] == vehicle) &
    (df["time_start_dt"] <= now_time) &
    (df["time_end_dt"] >= now_time)
]

if active_row.empty:
    active_row = df[df["vehicle_id"] == vehicle].iloc[[0]]

location_default = active_row["current_location"].values[0]
status_default = active_row["status"].values[0]
remarks_default = active_row["remarks"].values[0]

with st.form("driver_update"):
    location = st.text_input(
        "Current Location / Site Code",
        value=location_default,
        placeholder="e.g. P201, P202, Dormitory, On road"
    )

    status = st.selectbox(
        "Status",
        ["Available", "Busy"],
        index=0 if status_default == "Available" else 1
    )

    remarks = st.text_input("Remarks", value=remarks_default)

    submit = st.form_submit_button("Update Whereabout")

# -------------------------
# SAVE UPDATE (Persistent)
# -------------------------
if submit:
    mask = (
        (df["vehicle_id"] == vehicle) &
        (df["time_start_dt"] <= now_time) &
        (df["time_end_dt"] >= now_time)
    )

    if df[mask].empty:
        st.error("❌ No active time slot found.")
    else:
        df.loc[mask, "current_location"] = location
        df.loc[mask, "status"] = status
        df.loc[mask, "remarks"] = remarks
        df.loc[mask, "last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")

        save_data(df)
        st.success("✅ Whereabout updated and saved (persistent).")

# -------------------------
# AVAILABLE NOW
# -------------------------
st.subheader("🟢 Available Now")

available_now = df[
    (df["status"] == "Available") &
    (df["time_start_dt"] <= now_time) &
    (df["time_end_dt"] >= now_time)
]

if available_now.empty:
    st.warning("No pick-up lorry available now.")
else:
    st.dataframe(
        available_now[
            ["vehicle_id", "plate_no", "driver",
             "current_location", "time_start", "time_end",
             "remarks", "last_updated"]
        ],
        use_container_width=True
    )

# -------------------------
# TODAY'S SCHEDULE
# -------------------------
st.subheader("📅 Today's Pick-up Lorry Schedule")

vehicle_filter = st.multiselect(
    "Filter by Vehicle",
    df["vehicle_id"].unique(),
    default=df["vehicle_id"].unique()
)

filtered_df = df[df["vehicle_id"].isin(vehicle_filter)].copy()

filtered_df["active_now"] = filtered_df.apply(
    lambda r: "✅ Active" if r["time_start_dt"] <= now_time <= r["time_end_dt"] else "",
    axis=1
)

st.dataframe(
    filtered_df.sort_values(["vehicle_id", "time_start"])[
        ["vehicle_id", "plate_no", "driver",
         "current_location", "status",
         "time_start", "time_end",
         "remarks", "last_updated", "active_now"]
    ],
    use_container_width=True
)

