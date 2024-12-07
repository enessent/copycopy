from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    api_key = os.environ.get("HELIUS_API_KEY", "not_set")
    return {
        "status": "healthy",
        "helius_key_status": "set" if api_key != "not_set" else "not_set"
    }
