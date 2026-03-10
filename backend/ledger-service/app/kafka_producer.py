from kafka import KafkaProducer
import json
import os

producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)


def send_transaction_event(user, amount, tx_type):

    event = {
        "event": "transaction.created",
        "user": user,
        "amount": amount,
        "type": tx_type
    }

    producer.send("transactions", event)