from bytewax.dataflow import Dataflow
from bytewax.connectors.kafka import KafkaSource
from bytewax.operators import input, map, sink
import json
import os

os.makedirs("data", exist_ok=True)

flow = Dataflow("sensor-pipeline")

source = KafkaSource(
    brokers=["kafka:9092"],
    topics=["sensor-data"],
    group_id="bytewax-group"
)

stream = input("input", flow, source)
stream = map(stream, mapper=lambda kv: json.loads(kv[1]))

def file_sink(_worker_index, _worker_count):
    def write_json(record):
        with open("data/latest.json", "w") as f:
            json.dump(record, f)
    return write_json

sink(stream, file_sink)