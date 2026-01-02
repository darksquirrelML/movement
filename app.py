#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd

# -------------------------
# Page config
# -------------------------
st.set_page_config(
    page_title="Company Vehicle Dashboard",
    page_icon="🚚",
    layout="wide"
)

st.title("🚚 Company Vehicle Movement Dashboard")

# -------------------------
# Load data
# -------------------------
@st.cache_data
def load_data():
    return pd.read_csv("data/vehicles.csv")

df = load_data()

# -------------------------
# Filters
# -------------------------
st.sidebar.header("🔎 Filters")

vehicle_type = st.sidebar.multiselect(
    "Vehicle Type",
    options=df["vehicle_type"].unique(),
    default=df["vehicle_type"].unique()
)

status = st.sidebar.multiselect(
    "Status",
    options=df["status"].unique(),
    default=df["status"].unique()
)

filtered_df = df[
    (df["vehicle_type"].isin(vehicle_type)) &
    (df["status"].isin(status))
]

# -------------------------
# KPIs
# -------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Vehicles", len(df))
col2.metric("Available", len(df[df["status"] == "Available"]))
col3.metric("In Use", len(df[df["status"] == "In Use"]))

# -------------------------
# Vehicle table
# -------------------------
st.subheader("📋 Vehicle Status")

st.dataframe(
    filtered_df,
    use_container_width=True
)

# -------------------------
# Simple booking info (view only)
# -------------------------
st.subheader("📝 Vehicle Details")

selected_vehicle = st.selectbox(
    "Select Vehicle",
    filtered_df["vehicle_id"]
)

vehicle_info = filtered_df[
    filtered_df["vehicle_id"] == selected_vehicle
].iloc[0]

st.write(f"""
**Vehicle Type:** {vehicle_info['vehicle_type']}  
**Plate No:** {vehicle_info['plate_no']}  
**Location:** {vehicle_info['current_location']}  
**Status:** {vehicle_info['status']}  
**Assigned To:** {vehicle_info['assigned_to']}  
**Purpose:** {vehicle_info['purpose']}  
**Last Update:** {vehicle_info['last_update']}
""")

