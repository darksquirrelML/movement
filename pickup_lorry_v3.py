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
    page_title="Pick-up Lorry Dashboard",
    page_icon="🚐",
    layout="wide"
)

st.title("🚐 Pick-up Lorry Availability & Whereabout")

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
# Timezone (Singapore)
# -------------------------
SG_TZ = pytz.timezone("Asia/Singapore")
now_dt = datetime.now(SG_TZ)
now_str = now_dt.strftime("%H:%M")  # HH:MM string for comparison

st.caption(f"🕒 Current Time (SG): **{now_str}**")

# -------------------------
# Load data
# -------------------------
df = load_data()

# # Immediately after loading data from SQLite
# df = load_data()

# Normalize times to HH:MM
df["time_start"] = df["time_start"].str.slice(0,5)
df["time_end"] = df["time_end"].str.slice(0,5)


# -------------------------
# DRIVER WHEREABOUT UPDATE
# -------------------------
st.subheader("📍 Driver Whereabout Update (Auto-Save)")

vehicle = st.selectbox("Vehicle", df["vehicle_id"].unique())

vehicle_df = df[df["vehicle_id"] == vehicle].copy()

# Find active slot or next slot
active_slot = vehicle_df[
    (vehicle_df["time_start"] <= now_str) &
    (vehicle_df["time_end"] >= now_str)
]

if active_slot.empty:
    upcoming = vehicle_df[vehicle_df["time_start"] > now_str].sort_values("time_start")
    target_slot = upcoming.iloc[[0]] if not upcoming.empty else vehicle_df.iloc[[0]]
else:
    target_slot = active_slot

# Pre-fill form fields
location_default = target_slot["current_location"].values[0]
status_default = target_slot["status"].values[0]
remarks_default = target_slot["remarks"].values[0]

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

# Save update
if submit:
    idx = target_slot.index
    df.loc[idx, "current_location"] = location
    df.loc[idx, "status"] = status
    df.loc[idx, "remarks"] = remarks
    df.loc[idx, "last_updated"] = now_dt.strftime("%Y-%m-%d %H:%M")

    save_data(df)
    df = load_data()  # reload updated data

    st.success("✅ Whereabout updated successfully and reflected in schedule.")

# -------------------------
# AVAILABLE NOW
# -------------------------
st.subheader("🟢 Available Now")

available_now = df[
    (df["status"] == "Available") &
    (df["time_start"] <= now_str) &
    (df["time_end"] >= now_str)
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

# Highlight active now
filtered_df["active_now"] = filtered_df.apply(
    lambda r: "✅ Active" if r["time_start"] <= now_str <= r["time_end"] else "",
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

