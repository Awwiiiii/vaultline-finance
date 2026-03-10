import os
import json
import time
import psycopg2
import jwt

from kafka import KafkaProducer

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from prometheus_fastapi_instrumentator import Instrumentator


app = FastAPI()

# -----------------------------
# Prometheus Metrics
# -----------------------------
Instrumentator().instrument(app).expose(app)

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Environment
# -----------------------------
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "transactions")

# -----------------------------
# Security
# -----------------------------
security = HTTPBearer()

# -----------------------------
# Database config
# -----------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# -----------------------------
# Kafka Producer (Retry Safe)
# -----------------------------
producer = None

def get_kafka_producer():

    global producer

    while producer is None:
        try:

            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=5
            )

            print("Connected to Kafka")

        except Exception:
            print("Kafka not ready, retrying in 5 seconds...")
            time.sleep(5)

    return producer


# -----------------------------
# JWT Verification
# -----------------------------
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# -----------------------------
# Transaction Model
# -----------------------------
class Transaction(BaseModel):
    user: str
    amount: float
    type: str
    description: str = ""


# -----------------------------
# Kafka Event Sender
# -----------------------------
def send_transaction_event(user, amount, tx_type):

    event = {
        "event": "transaction.created",
        "user": user,
        "amount": amount,
        "type": tx_type
    }

    producer = get_kafka_producer()

    producer.send(KAFKA_TOPIC, event)
    producer.flush()


# -----------------------------
# Database Connection Helper
# -----------------------------
def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")


# -----------------------------
# Create Transaction
# -----------------------------
@app.post("/api/v1/transaction")
def create_transaction(tx: Transaction, user=Depends(verify_token)):

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, balance FROM accounts WHERE owner_name=%s",
            (tx.user,)
        )

        acc = cur.fetchone()

        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")

        account_id = acc[0]
        balance = float(acc[1])

        if tx.type == "withdraw":
            balance -= tx.amount
        else:
            balance += tx.amount

        cur.execute(
            "UPDATE accounts SET balance=%s WHERE id=%s",
            (balance, account_id)
        )

        cur.execute(
            """
            INSERT INTO transactions
            (account_id, type, amount, description)
            VALUES (%s,%s,%s,%s)
            """,
            (account_id, tx.type, tx.amount, tx.description)
        )

        conn.commit()

        send_transaction_event(tx.user, tx.amount, tx.type)

        return {
            "status": "transaction processed",
            "user": tx.user,
            "amount": tx.amount,
            "type": tx.type
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()


# -----------------------------
# Get Account
# -----------------------------
@app.get("/api/v1/account/{owner}")
def get_account_data(owner: str, user=Depends(verify_token)):

    conn = None
    cur = None

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, owner_name, balance FROM accounts WHERE owner_name=%s",
            (owner,)
        )

        acc = cur.fetchone()

        if not acc:
            raise HTTPException(status_code=404, detail="Account not found")

        cur.execute(
            """
            SELECT type, amount, description, created_at
            FROM transactions
            WHERE account_id=%s
            ORDER BY created_at DESC
            LIMIT 5
            """,
            (acc[0],)
        )

        rows = cur.fetchall()

        transactions = [
            {
                "type": r[0],
                "amount": float(r[1]),
                "note": r[2],
                "date": str(r[3])
            }
            for r in rows
        ]

        return {
            "owner": acc[1],
            "balance": float(acc[2]),
            "transactions": transactions,
            "db_status": "Verified: PostgreSQL Storage"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:

        if cur:
            cur.close()

        if conn:
            conn.close()