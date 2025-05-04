#!/bin/bash

# Start Zookeeper in the background
echo "🔄 Starting Zookeeper..."
/etc/confluent/docker/run &

# Wait for Zookeeper to be up
echo "⏳ Waiting for Zookeeper to start..."
sleep 10

# Start Kafka
echo "🚀 Starting Kafka..."
/etc/confluent/docker/run
# Wait for Kafka to be up