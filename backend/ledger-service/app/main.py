from fastapi import FastAPI
from kafka_producer import send_transaction_event

app = FastAPI()


@app.post("/deposit")
def deposit(user: str, amount: float):

    # store in DB (your existing logic)

    send_transaction_event(user, amount, "deposit")

    return {
        "status": "success",
        "message": "deposit completed"
    }