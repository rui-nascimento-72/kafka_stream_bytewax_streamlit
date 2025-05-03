# --- app.py ---
import json
import pandas as pd
import streamlit as st
import time
import altair as alt


st.set_page_config("📦 Order Dashboard", layout="wide")
st.title("📦 Real-Time Order Dashboard")

LATEST_PATH = "data/latest.json"
METRICS_PATH = "data/metrics.json"
WINDOWS_PATH = "data/windows.json"

# -- Load Metrics
try:
    with open(METRICS_PATH) as f:
        metrics = json.load(f)

    st.subheader("📈 Key Metrics")
    col1, col2 = st.columns(2)
    col1.metric("🧾 Total Orders", metrics["order_count"])
    col2.metric("🧍 Clients", len(metrics["orders_by_client"]))

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

# -- Load Latest Orders
try:
    with open(LATEST_PATH) as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    if "timestamp" not in df or df.empty:
        st.warning("⚠️ No timestamp data in latest.json.")
        st.stop()

    df["order_id"] = df["order_id"].astype(str)

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
    df = df.dropna(subset=["timestamp"])

    st.subheader("🧾 Latest Orders")
    st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)

    # -- 1-Minute Rolling Window Chart
    df["window"] = df["timestamp"].dt.floor("1min")
    windowed = df.groupby("window")["quantity"].sum().reset_index()

    st.subheader("🪟 Quantity per 1-Minute Window")
    line = alt.Chart(windowed).mark_line(point=True).encode(
        x="window:T",
        y="quantity:Q"
    ).properties(height=300)
    st.altair_chart(line, use_container_width=True)

    # -- Histogram
    # -- Histogram with Altair
    st.subheader("📊 Histogram of Order Quantities")
    quantity_hist_df = df["quantity"].value_counts().reset_index()
    quantity_hist_df.columns = ["quantity", "count"]
    quantity_hist_df = quantity_hist_df.sort_values("quantity")

    hist_chart = alt.Chart(quantity_hist_df).mark_bar().encode(
        x=alt.X("quantity:O", title="Quantity"),
        y=alt.Y("count:Q", title="Number of Orders")
    ).properties(
      height=300,
       title="Histogram of Order Quantities"
    )

    st.altair_chart(hist_chart, use_container_width=True)


except Exception as e:
    st.error(f"❌ Failed to load order data: {e}")

# -- Load Windowed Aggregates
try:
    with open(WINDOWS_PATH) as f:
        window_data = json.load(f)

    window_df = pd.DataFrame(window_data)
    window_df["start"] = pd.to_datetime(window_df["start"], errors="coerce")
    window_df["end"] = pd.to_datetime(window_df["end"], errors="coerce")
    window_df = window_df.dropna(subset=["start", "end"])

    st.subheader("🪟 Aggregated Window Metrics")
    st.line_chart(window_df.set_index("start")[["order_count", "total_quantity"]])

except Exception as e:
    st.warning(f"⚠️ Could not load windowed data: {e}")

# -- Refresh controls
if st.button("🔁 Refresh"):
    st.rerun()

time.sleep(10)
st.rerun()
