# 📦 Real-Time Order Analytics with Bytewax + Streamlit

This project demonstrates a real-time data pipeline using:

- [Bytewax](https://www.bytewax.io/) for stateful stream processing
- [Apache Kafka](https://kafka.apache.org/) as the data source
- [Streamlit](https://streamlit.io/) for interactive dashboards

All services are containerized with Docker and run with a single `docker-compose` command.

---
## 🚀 Getting Started

### 1. 📦 Prerequisites

- Docker & Docker Compose installed

### 2. 🛠️ Build and Run

```bash
docker-compose up --build

This will start:

Kafka + Zookeeper

A Bytewax worker running bytewax_processor.py

A Streamlit app accessible at http://localhost:8501

🧠 Bytewax Pipeline (bytewax_processor.py)
The pipeline does the following:

✅ Reads from a Kafka topic orders-data

✅ Parses JSON order events

✅ Stores all events to data/latest.json

✅ Maintains stateful metrics:

Total orders

Quantity per client

Quantity per item

Stored in data/metrics.json

✅ Performs 5-minute tumbling window aggregation using fold_window

Output in data/windows.json

📊 Streamlit Dashboard (streamlit_app.py)
Access at http://localhost:8501

Features:
📈 Total orders and active clients

🏆 Top 10 clients and top 10 items

🧾 Raw order table (latest)

🪟 Real 5-minute windowed line chart (based on windows.json)

📊 Histogram of order quantities

Auto-refreshes every 10 seconds.


