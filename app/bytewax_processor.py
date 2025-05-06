# --- bytewax_processor.py ---
import os
import json
from datetime import timedelta, datetime, timezone
from confluent_kafka import OFFSET_BEGINNING

from bytewax.dataflow import Dataflow
from bytewax.connectors.kafka import KafkaSource
from bytewax.operators import input, map, filter as op_filter, inspect, key_on, stateful_map
from bytewax.operators.windowing import fold_window, TumblingWindower, EventClock

flow = Dataflow("orders-pipeline")

# --- Kafka Source ---
source = KafkaSource(
    brokers=["redpanda:9092"],
    topics=["orders-data"],
    tail=True,
    starting_offset=OFFSET_BEGINNING
)

stream = input("in", flow, source)

# --- STEP 1: Parse JSON safely ---
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
def normalize_timestamp(msg):
    ts = msg.get("timestamp")
    if ts:
        if ts > 1e12:
            msg["timestamp"] = ts / 1000.0
        elif ts > 1e9:
            msg["timestamp"] = float(ts)
    return msg

stream = map("normalize-ts", stream, normalize_timestamp)

# --- STEP 3: Save Raw Data ---
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

inspect("save-latest", stream, write_raw)

# --- STEP 4: Stateful Aggregation ---
keyed = key_on("agg-key", stream, lambda _: "global")

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

agg = stateful_map("agg", keyed, update)

def write_metrics(_step_id, item):
    _, metrics = item
    os.makedirs("data", exist_ok=True)
    with open("data/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

inspect("metrics", agg, write_metrics)

# --- STEP 5: 1-Minute Window Aggregation with Debug Logs ---
clock = EventClock(
    ts_getter=lambda msg: datetime.fromtimestamp(
        float(msg.get("timestamp", 0)), tz=timezone.utc
    ),
    wait_for_system_duration=timedelta(minutes=1)  # give some buffer for late events
)

windows = TumblingWindower(
    length=timedelta(minutes=1),
    align_to=datetime(2025, 1, 1, tzinfo=timezone.utc)
)

def fold(acc, msg):
    acc["order_count"] += 1
    acc["total_quantity"] += int(msg.get("quantity", 0))
    return acc

# Debug: show messages entering the fold_window
inspect("pre-window", keyed, lambda _id, msg: print("🧪 Window input:", msg))

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
