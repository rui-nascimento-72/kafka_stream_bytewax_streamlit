import os
import json
import pandas as pd
import streamlit as st
import time
import altair as alt

st.set_page_config("📦 Order Dashboard", layout="wide")

st.title("📦 Real-Time Order Dashboard")

LATEST_PATH = "data/latest.json"
METRICS_PATH = "data/metrics.json"

# -- Load Metrics (aggregations)
try:
    with open(METRICS_PATH) as f:
        metrics = json.load(f)

    st.subheader("📈 Key Metrics")
    col1, col2 = st.columns(2)
    col1.metric("🧾 Total Orders", metrics["order_count"])
    col2.metric("🧍 Clients", len(metrics["orders_by_client"]))

    # --- Top clients chart
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

# -- Load Raw Order Stream
try:
    with open(LATEST_PATH) as f:
        data = json.load(f)

    if not isinstance(data, list):
        st.warning("⚠️ Data is not a list.")
        st.stop()

    df = pd.DataFrame(data)

    st.subheader("🧾 Latest Orders")
    st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)

except Exception as e:
    st.error(f"❌ Failed to load order data: {e}")

# -- Refresh
if st.button("🔁 Refresh"):
    st.rerun()
# -- Auto-refresh every 10 seconds
time.sleep(10)
st.rerun()