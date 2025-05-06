from kafka import KafkaProducer
import json
import time
import random
import uuid

while True:
    try:
        
        producer = KafkaProducer(
                            bootstrap_servers='redpanda:9092',
                            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        break
    except Exception as e:
        print(f"Redpanda not available, retrying... ({e})")
        time.sleep(10)

while True:
    event = {
        "order_id": str(uuid.uuid4().int),
        "item_id": random.randint(1, 1000),
        "client_id": random.randint(1, 100),
        "quantity": random.randint(1, 5),
        "timestamp": time.time()
    }
    producer.send("orders-data", value=event)
    print("Sent:", event)
    time.sleep(10)