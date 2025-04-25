
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
        "order_id": int(time.time() * 1000),
        "book_reference": random.randint(1, 1000),
        "quantity": random.randint(1, 5),
        "timestamp": time.time()
    }
    producer.send('book-orders', value=event)
    print("Sent:", event)
    time.sleep(2)
