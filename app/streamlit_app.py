import os
import json
import pandas as pd
import streamlit as st
import time
import altair as alt
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config("📦 Order Dashboard", layout="wide")
st.title("📦 Real-Time Order Dashboard")

LATEST_PATH = "data/latest.json"
METRICS_PATH = "data/metrics.json"
WINDOWS_PATH = "data/windows.json"

# -- Load Aggregated Metrics --
try:
    with open(METRICS_PATH) as f:
        metrics = json.load(f)

    st.subheader("📈 Key Metrics")
    col1, col2 = st.columns(2)
    col1.metric("🧾 Total Orders", metrics["order_count"])
    col2.metric("🧍 Clients", len(metrics["orders_by_client"]))

    # --- Top Clients & Items
    clients_df = pd.DataFrame(
        list(metrics["orders_by_client"].items()),
        columns=["client_id", "total_quantity"]
    ).sort_values("total_quantity", ascending=False)

    items_df = pd.DataFrame(
        list(metrics["orders_by_item"].items()),
        columns=["item_id", "total_quantity"]
    ).sort_values("total_quantity", ascending=False)

    st.subheader("🏆 Top Clients & Items")
    col1, col2 = st.columns(2)

    with col1:
        st.altair_chart(
            alt.Chart(clients_df.head(10))
            .mark_bar()
            .encode(x="client_id:O", y="total_quantity:Q")
            .properties(height=300, title="Top Clients"),
            use_container_width=True
        )

    with col2:
        st.altair_chart(
            alt.Chart(items_df.head(10))
            .mark_bar()
            .encode(x="item_id:O", y="total_quantity:Q")
            .properties(height=300, title="Top Items"),
            use_container_width=True
        )

except Exception as e:
    st.warning(f"⚠️ Could not load metrics: {e}")

# -- Load and Show Latest Orders --
try:
    with open(LATEST_PATH) as f:
        data = json.load(f)

    if not isinstance(data, list):
        st.warning("⚠️ Order data is not a list.")
        st.stop()

    df = pd.DataFrame(data)

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
        st.subheader("🧾 Latest Orders")
        st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)
    else:
        st.info("ℹ️ No orders to show.")

except Exception as e:
    st.error(f"❌ Failed to load order data: {e}")

# -- Load and Show Real Windowed Aggregates --
try:
    with open(WINDOWS_PATH) as f:
        windows_data = json.load(f)

    if isinstance(windows_data, list) and windows_data:
        window_df = pd.DataFrame(windows_data)
        window_df["start"] = pd.to_datetime(window_df["start"])
        window_df["end"] = pd.to_datetime(window_df["end"])

        st.subheader("🪟 Real 5-Minute Windowed Totals")
        st.altair_chart(
            alt.Chart(window_df)
            .mark_line(point=True)
            .encode(
                x="start:T",
                y="total_quantity:Q",
                tooltip=["start:T", "end:T", "order_count", "total_quantity"]
            )
            .properties(height=300, title="Total Quantity per 5-Min Window"),
            use_container_width=True
        )
    else:
        st.info("ℹ️ No windowed data available yet.")

except Exception as e:
    st.warning(f"⚠️ Could not load windowed data: {e}")

# -- Histogram of Quantities --
try:
    if not df.empty:
        st.subheader("📊 Histogram of Order Quantities")
        fig, ax = plt.subplots()
        ax.hist(df["quantity"], bins=range(1, df["quantity"].max() + 2), edgecolor="black")
        ax.set_xlabel("Quantity")
        ax.set_ylabel("Number of Orders")
        st.pyplot(fig)
except Exception as e:
    st.warning(f"⚠️ Could not generate histogram: {e}")

# -- Refresh Controls --
st.markdown("---")
if st.button("🔁 Refresh Now"):
    st.rerun()

time.sleep(10)
st.rerun()
