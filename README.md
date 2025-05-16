# Kafka Stream Processing with Bytewax, Redpanda, and Streamlit

This project demonstrates a real-time data processing pipeline using Python 3.11, Docker, Bytewax, Redpanda, and Streamlit. The pipeline ingests simulated order data, processes it using Bytewax, and visualizes the results in a Streamlit dashboard.

## Features

- **Data Ingestion**: Simulated order data is produced using Kafka.
- **Stream Processing**: Bytewax processes the data in real-time, performing aggregations and windowing.
- **Visualization**: Streamlit provides a live dashboard to display metrics and trends.
- **Lightweight Kafka Alternative**: Redpanda is used as the Kafka broker for simplicity and performance.

---

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Visual Studio Code (recommended for development)
- Basic knowledge of Kafka, Bytewax, and Streamlit

## Getting Started
1. Clone the Repository

git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

2. Install Python Dependencies
Ensure you have Python 3.11 installed. Use a virtual environment:

python3.11 -m venv venv
source venv/bin/activate

pip install -r [requirements.bytewax.txt](http://_vscodecontentref_/14)
pip install -r [requirements.producer.txt](http://_vscodecontentref_/15)
pip install -r [requirements.streamlit.txt](http://_vscodecontentref_/16)

3. Run with Docker Compose
Build and start the services using Docker Compose:
docker-compose up --build

This will start the following services:

Redpanda: Kafka-compatible broker
Bytewax: Stream processing pipeline
Kafka Producer: Simulates order data
Streamlit: Dashboard for visualization

Access the Streamlit dashboard at http://localhost:8501.

## Documentation
## Bytewax
Bytewax is a Python framework for building stateful stream processing applications. It integrates with Kafka and supports advanced features like windowing and stateful aggregations.

Key components in this project:

KafkaSource: Reads data from Redpanda.

TumblingWindower: Performs 1-minute window aggregations.

Stateful Aggregation: Tracks metrics like total orders and quantities.

## Redpanda

Redpanda is a Kafka-compatible streaming platform designed for simplicity and performance. It replaces traditional Kafka brokers in this project.

## Streamlit
Streamlit is a Python library for building interactive dashboards. It is used to visualize real-time metrics and trends from the processed data.

## Development with Visual Studio Code
Install the Python and Docker extensions.

Open the project folder in VS Code.

Use the integrated terminal to run Python scripts or Docker commands.

Debug Streamlit apps directly in VS Code.

Forking and Contributing

Fork the repository on GitHub.

Create a new branch for your feature or bugfix.

Submit a pull request with a detailed description of your changes.

Troubleshooting

Redpanda not available: Ensure the redpanda service is running and accessible on port 9092.

Streamlit errors: Check the logs for missing data files or incorrect paths.

Bytewax issues: Verify the Kafka topic and broker configurations.

License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
Bytewax Documentation
Redpanda Documentation
Streamlit Documentation

