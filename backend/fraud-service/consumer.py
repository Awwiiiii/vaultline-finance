import json
import os
import time
from kafka import KafkaConsumer


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
KAFKA_GROUP = os.getenv("KAFKA_GROUP_ID", "fraud-service-group")
KAFKA_OFFSET_RESET = os.getenv("KAFKA_OFFSET_RESET", "earliest")


def create_consumer():

    while True:

        try:

            print("Connecting to Kafka...", flush=True)
            print(f"Bootstrap: {KAFKA_BOOTSTRAP_SERVERS}", flush=True)
            print(f"Topic: {KAFKA_TOPIC}", flush=True)
            print(f"Group: {KAFKA_GROUP}", flush=True)

            consumer = KafkaConsumer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_GROUP,
                auto_offset_reset=KAFKA_OFFSET_RESET,
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            )

            consumer.subscribe([KAFKA_TOPIC])

            print("✅ Fraud Service Connected to Kafka", flush=True)

            return consumer

        except Exception as e:

            print("Kafka not ready yet...", flush=True)
            print(e, flush=True)

            time.sleep(5)


def start_consumer():

    consumer = create_consumer()

    print("🚨 Fraud Service Listening for transactions...", flush=True)

    while True:

        records = consumer.poll(timeout_ms=1000)

        for topic_partition, messages in records.items():

            for message in messages:

                try:

                    data = message.value

                    print("Transaction Event:", data, flush=True)

                    amount = float(data.get("amount", 0))
                    user = data.get("user", "unknown")

                    if amount > 100000:
                        print(
                            f"⚠️ Possible Fraud Detected → user={user} amount={amount}",
                            flush=True
                        )

                except Exception as err:

                    print("Error processing event:", err, flush=True)


if __name__ == "__main__":
    start_consumer()