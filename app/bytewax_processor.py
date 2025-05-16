# --- bytewax_processor.py ---
# os, json, datetime: Standard Python libraries for file operations, JSON handling, and time manipulation.
# confluent_kafka: Used to define Kafka offsets.
# bytewax.dataflow: Core Bytewax class for defining a dataflow pipeline.
# bytewax.connectors.kafka: Provides Kafka integration for Bytewax.
# bytewax.operators: Includes operators for transforming and processing data in the pipeline.
# bytewax.operators.windowing: Provides tools for window-based aggregations.
import os
import json
from datetime import timedelta, datetime, timezone
from confluent_kafka import OFFSET_BEGINNING
from bytewax.dataflow import Dataflow
from bytewax.connectors.kafka import KafkaSource
from bytewax.operators import input, map, filter as op_filter, inspect, key_on, stateful_map
from bytewax.operators.windowing import fold_window, TumblingWindower, EventClock
#Initializes a Bytewax Dataflow named "orders-pipeline", which defines the processing pipeline.
flow = Dataflow("orders-pipeline")

# --- Kafka Source ---
#KafkaSource: Configures the Kafka source with:
#brokers: Kafka broker address.
#topics: Topic to consume messages from.
#tail: Whether to consume new messages as they arrive.
#starting_offset: Start consuming from the beginning of the topic.

source = KafkaSource(
    brokers=["redpanda:9092"],
    topics=["orders-data"],
    tail=True,
    starting_offset=OFFSET_BEGINNING
)
#input: Adds the Kafka source to the dataflow.

stream = input("in", flow, source)

# --- STEP 1: Parse JSON safely ---
# parse: Safely parses Kafka messages as JSON. If parsing fails, it logs an error and returns None.
# map: Applies the parse function to each message in the stream.
# op_filter: Filters out None values from the stream.
def parse(msg):
    try:
        if not msg.value:
            return None
        return json.loads(msg.value)
    except Exception as e:
        print("❌ Parse error:", e)
        return None

stream = map("parse", stream, parse)
stream = op_filter("drop-none", stream, lambda x: x is not None)

# --- STEP 2: Normalize Timestamps ---
# normalize_timestamp: Converts timestamps to seconds if they are in milliseconds or nanoseconds.
def normalize_timestamp(msg):
    ts = msg.get("timestamp")
    if ts:
        if ts > 1e12:
            msg["timestamp"] = ts / 1000.0
        elif ts > 1e9:
            msg["timestamp"] = float(ts)
    return msg
# map: Applies the normalization function to each message
stream = map("normalize-ts", stream, normalize_timestamp)

# --- STEP 3: Save Raw Data ---
# write_raw: Saves the latest processed messages to data/latest.json.
# Creates the data directory if it doesn't exist.
# Appends the new message to the existing JSON file.
def write_raw(_step_id, msg):
    os.makedirs("data", exist_ok=True)
    path = "data/latest.json"

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append(msg)

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

#inspect: Executes the write_raw function for each message in the stream.
inspect("save-latest", stream, write_raw)

# --- STEP 4: Stateful Aggregation ---
# key_on: Assigns all messages to a single key ("global") for aggregation.
keyed = key_on("agg-key", stream, lambda _: "global")

# update: Updates the state with:
# Total order count.
# Orders grouped by client and item.

def update(state, msg):
    if state is None:
        state = {
            "order_count": 0,
            "orders_by_client": {},
            "orders_by_item": {}
        }

    client_id = str(msg.get("client_id"))
    item_id = str(msg.get("item_id"))
    qty = int(msg.get("quantity", 1))

    state["order_count"] += 1
    state["orders_by_client"][client_id] = state["orders_by_client"].get(client_id, 0) + qty
    state["orders_by_item"][item_id] = state["orders_by_item"].get(item_id, 0) + qty

    return state, state

# stateful_map: Applies the update function to maintain state across messages.

agg = stateful_map("agg", keyed, update)

# write_metrics: Writes aggregated metrics to data/metrics.json.
def write_metrics(_step_id, item):
    _, metrics = item
    os.makedirs("data", exist_ok=True)
    with open("data/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

inspect("metrics", agg, write_metrics)

# --- STEP 5: 1-Minute Window Aggregation with Debug Logs ---
#EventClock: Extracts timestamps from messages and waits for late events.
clock = EventClock(
    ts_getter=lambda msg: datetime.fromtimestamp(
        float(msg.get("timestamp", 0)), tz=timezone.utc
    ),
    wait_for_system_duration=timedelta(minutes=1)  # give some buffer for late events
)

#TumblingWindower: Defines 1-minute windows aligned to a specific start time.
windows = TumblingWindower(
    length=timedelta(minutes=1),
    align_to=datetime(2025, 1, 1, tzinfo=timezone.utc)
)

#fold: Aggregates data within each window.
def fold(acc, msg):
    acc["order_count"] += 1
    acc["total_quantity"] += int(msg.get("quantity", 0))
    return acc

# Debug: show messages entering the fold_window
inspect("pre-window", keyed, lambda _id, msg: print("🧪 Window input:", msg))

#fold_window: Applies the folding logic to the windowed data.
windowed = fold_window(
    "win",
    keyed,
    clock,
    windows,
    lambda: {"order_count": 0, "total_quantity": 0},
    fold,
    lambda a, b: {
        "order_count": a["order_count"] + b["order_count"],
        "total_quantity": a["total_quantity"] + b["total_quantity"]
    }
)

#write_window: Writes windowed results to data/windows.json.
def write_window(_step_id, item):
    print("📥 Received window item:", item)

    try:
        key, (start_ts, data) = item
        print("📥 Start time stamp", start_ts)
        start_dt = datetime.fromtimestamp(start_ts, tz=timezone.utc)
    except Exception as e:
        print(f"⚠️ Invalid window start: {item} — {e}")
        return

    end_dt = start_dt + timedelta(minutes=1)

    os.makedirs("data", exist_ok=True)
    path = "data/windows.json"
    print(f"📁 Writing to: {os.path.abspath(path)}")

    try:
        with open(path, "r") as f:
            existing = json.load(f)
    except Exception as e:
        print(f"⚠️ Couldn't read windows.json: {e}")
        existing = []

    try:
        new_entry = {
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat(),
            "order_count": data["order_count"],
            "total_quantity": data["total_quantity"]
        }
        existing.append(new_entry)

        with open(path, "w") as f:
            json.dump(existing, f, indent=2)

        print("🪟 Wrote window:", new_entry)
    except Exception as e:
        print(f"❌ Failed to write window: {e}")

inspect("window", windowed.down, write_window)
