import os
import json
from confluent_kafka import OFFSET_BEGINNING
from bytewax.dataflow import Dataflow
from bytewax.connectors.kafka import KafkaSource
from bytewax.operators import input, map, filter as op_filter, inspect
from bytewax.operators import key_on, stateful_map

flow = Dataflow("orders-pipeline")

# --- Kafka Source ---
source = KafkaSource(
    brokers=["localhost:9092"],
    topics=["orders-data"],
    tail=True,
    starting_offset=OFFSET_BEGINNING
)

stream = input("in", flow, source)

# --- STEP 1: Parse messages safely ---
def parse(msg):
    try:
        if not msg.value:
            print("⚠️ Skipped empty")
            return None
        parsed = json.loads(msg.value)
        print("📥 Raw:", parsed)
        return parsed
    except Exception as e:
        print("❌ Parse error:", msg.value, "|", e)
        return None

stream = map("parse", stream, parse)
stream = op_filter("not-none", stream, lambda x: x is not None)

# --- STEP 2: Save every message to file ---
def write_to_file(_step_id, msg):
    os.makedirs("data", exist_ok=True)
    path = "data/latest.json"

    try:
        with open(path, "r") as f:
            data = json.load(f)
            if not isinstance(data, list):
                data = [data]
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append(msg)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    print("✅ Appended:", msg)

inspect("save", stream, write_to_file)

# --- STEP 3: Aggregations using stateful_map ---
# First, key the stream to ensure all items are processed together
keyed_stream = key_on("key", stream, lambda _: "global")

def update_state(state, msg):
    if state is None:
        state = {
            "order_count": 0,
            "orders_by_client": {},
            "orders_by_item": {}
        }

    state["order_count"] += 1

    client_id = str(msg.get("client_id"))
    item_id = str(msg.get("item_id"))
    quantity = int(msg.get("quantity", 1))

    state["orders_by_client"][client_id] = state["orders_by_client"].get(client_id, 0) + quantity
    state["orders_by_item"][item_id] = state["orders_by_item"].get(item_id, 0) + quantity

    return state, state  # (new_state, output)

metrics = stateful_map("agg", keyed_stream, update_state)

# --- STEP 4: Write metrics to JSON for Streamlit ---
def write_metrics(_step_id, item):
    _, metrics = item  # item is (key, state)
    
    os.makedirs("data", exist_ok=True)
    path = "data/metrics.json"

    def to_dict(d):
        return dict(d) if isinstance(d, dict) else d

    serializable = {
        "order_count": metrics["order_count"],
        "orders_by_client": to_dict(metrics["orders_by_client"]),
        "orders_by_item": to_dict(metrics["orders_by_item"]),
    }

    with open(path, "w") as f:
        json.dump(serializable, f, indent=2)

    print("📊 Updated metrics")

inspect("metrics", metrics, write_metrics)
