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
    brokers=["kafka:9092"],
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

# --- STEP 2: Save to file ---
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

# --- STEP 3: Stateful Aggregation ---
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

# --- STEP 4: 5-Minute Window Aggregation ---
# Use timestamp from event
clock = EventClock(
    ts_getter=lambda msg: datetime.fromtimestamp(msg["timestamp"], tz=timezone.utc),
    wait_for_system_duration=timedelta(seconds=0)
)

windows = TumblingWindower(
    length=timedelta(minutes=5),
    align_to=datetime(2025, 1, 1, tzinfo=timezone.utc)
)

windowed = fold_window(
    "win",
    keyed,
    clock,
    windows,
    lambda: {"order_count": 0, "total_quantity": 0},
    lambda acc, msg: {
        "order_count": acc["order_count"] + 1,
        "total_quantity": acc["total_quantity"] + int(msg.get("quantity", 0))
    },
    lambda a, b: {
        "order_count": a["order_count"] + b["order_count"],
        "total_quantity": a["total_quantity"] + b["total_quantity"]
    }
)

def write_window(_step_id, item):
    start_str, data = item  # Bytewax 0.21.1 returns start_time as str
    os.makedirs("data", exist_ok=True)
    path = "data/windows.json"

    try:
        with open(path, "r") as f:
            existing = json.load(f)
    except:
        existing = []

    existing.append({
        "start": start_str,
        "end": start_str,
        "order_count": data["order_count"],
        "total_quantity": data["total_quantity"]
    })

    with open(path, "w") as f:
        json.dump(existing, f, indent=2)

    print("🪟 Wrote window:", start_str)

inspect("window", windowed.down, write_window)
