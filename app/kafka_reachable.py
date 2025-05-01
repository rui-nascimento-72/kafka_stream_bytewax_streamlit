from confluent_kafka import Consumer, TopicPartition, OFFSET_BEGINNING

conf = {
    "bootstrap.servers": "kafka:9092",
    "group.id": "debugger",
    "auto.offset.reset": "earliest"
}

consumer = Consumer(conf)
consumer.assign([TopicPartition("orders-data", 0, OFFSET_BEGINNING)])

print("⏳ Waiting for message...")
msg = consumer.poll(5.0)
if msg is None:
    print("❌ No message received.")
elif msg.error():
    print("❌ Kafka error:", msg.error())
else:
    print("✅ Got message:", msg.value())