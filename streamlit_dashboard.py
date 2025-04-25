
import streamlit as st
import json
import os
import time

st.set_page_config(page_title="Live Sensor Dashboard", layout="centered")
st.title("📡 Live Sensor Data")

placeholder = st.empty()

while True:
    try:
        if os.path.exists("data/latest.json"):
            with open("data/latest.json") as f:
                data = json.load(f)
                placeholder.json(data)
        time.sleep(1)
    except Exception as e:
        st.error(f"Error reading data: {e}")
        time.sleep(1)
