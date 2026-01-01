from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="VaultLine Finance Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "Operational", "vault_load": "normal"}

@app.get("/api/v1/account")
def get_account_data():
    return {
        "owner": "Awi2005",
        "balance": 154200.50,
        "currency": "USD",
        "last_transaction": "+$5,000.00 from AWS"
    }