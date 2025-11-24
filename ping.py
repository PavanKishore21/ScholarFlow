# ping.py
from fastapi import FastAPI

api = FastAPI(title="Ping API")

@api.get("/health")
def health():
    return {"status": "ok"}
