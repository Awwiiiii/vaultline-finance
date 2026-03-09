import os
import psycopg2
import jwt

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secret for JWT verification
SECRET = "vaultline-secret"
ALGORITHM = "HS256"

# Swagger security
security = HTTPBearer()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "db"),  # docker service name
    "database": "vaultlinedb",
    "user": "postgres",
    "password": "vaultpass123"
}


# JWT verification
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):

    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        return payload

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/api/v1/account/{owner}")
def get_account_data(owner: str, user=Depends(verify_token)):

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Fetch account details
        cur.execute(
            "SELECT id, owner_name, balance FROM accounts WHERE owner_name = %s;",
            (owner,)
        )

        acc = cur.fetchone()

        if not acc:
            return {"error": "Account not found"}

        # Fetch transactions
        cur.execute("""
            SELECT type, amount, description, created_at
            FROM transactions
            WHERE account_id = %s
            ORDER BY created_at DESC
            LIMIT 5;
        """, (acc[0],))

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

        cur.close()
        conn.close()

        return {
            "owner": acc[1],
            "balance": float(acc[2]),
            "transactions": transactions,
            "db_status": "Verified: PostgreSQL Storage"
        }

    except Exception as e:
        return {
            "error": str(e),
            "db_status": "Database Offline"
        }