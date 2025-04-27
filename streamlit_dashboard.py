import streamlit as st
import json
import pandas as pd
import time
import os

st.set_page_config(page_title="📡 Sensor Dashboard", layout="wide")
st.title("📈 Live Sensor Data")

placeholder = st.empty()

while True:
    try:
        if os.path.exists("data/latest.json"):
            with open("data/latest.json") as f:
                data = json.load(f)
                df = pd.DataFrame([data])
                placeholder.dataframe(df)
    except Exception as e:
        st.error(f"Error reading data: {e}")
    time.sleep(2)