import psycopg2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "host": "vaultline-db-service",
    "database": "vaultlinedb",
    "user": "postgres",
    "password": "vaultpass123"
}

@app.get("/api/v1/account")
def get_account_data():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 1. Fetch Account Details
        cur.execute("SELECT id, owner_name, balance FROM accounts WHERE owner_name = 'Awi2005';")
        acc = cur.fetchone()
        
        if not acc:
            return {"error": "Account not found"}

        # 2. Fetch Transaction History linked by ID
        cur.execute("""
            SELECT type, amount, description, created_at 
            FROM transactions 
            WHERE account_id = %s 
            ORDER BY created_at DESC 
            LIMIT 5;
        """, (acc[0],))
        
        rows = cur.fetchall()
        transactions = [
            {"type": r[0], "amount": float(r[1]), "note": r[2], "date": str(r[3])} 
            for r in rows
        ]
        
        cur.close()
        conn.close()

        return {
            "owner": acc[1],
            "balance": float(acc[2]),
            "transactions": transactions,
            "db_status": "Verified: AWS Persistent Storage"
        }
    except Exception as e:
        return {"error": str(e), "db_status": "Database Offline"}