
from bytewax import Dataflow, run_main
from bytewax.connectors.kafka import KafkaSource
import json
import os

os.makedirs("data", exist_ok=True)

topic = "sensor-data"
brokers = ["kafka:9092"]
source = KafkaSource(brokers, topic, "bytewax-group")

flow = Dataflow()
flow.input("input", source)

def to_json_file(event):
    value = json.loads(event[1])
    with open("data/latest.json", "w") as f:
        json.dump(value, f)
    return value

flow.map(to_json_file)

if __name__ == "__main__":
    run_main(flow)
