from fastapi import FastAPI
from pydantic import BaseModel
import jwt
import datetime

app = FastAPI()

SECRET_KEY = "vaultline-secret"

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: LoginRequest):

    payload = {
        "user": data.username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return {
        "access_token": token,
        "token_type": "bearer"
    }
