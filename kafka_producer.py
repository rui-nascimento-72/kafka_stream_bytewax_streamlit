from kafka import KafkaProducer
import json
import time
import random

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

while True:
    event = {
        "sensor_id": random.randint(1, 5),
        "temperature": round(random.uniform(20, 30), 2),
        "humidity": round(random.uniform(40, 60), 2),
        "timestamp": time.time()
    }
    producer.send("sensor-data", value=event)
    print("Sent:", event)
    time.sleep(2)