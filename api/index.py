from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class WalletRequest(BaseModel):
    address: str
    timeframe: Optional[int] = 7

@app.get("/api/test")
def read_root():
    return {"message": "Hello World"}

@app.post("/api/analyze")
async def analyze_wallet(request: WalletRequest):
    try:
        api_key = os.environ.get("HELIUS_API_KEY")
        base_url = "https://api.helius.xyz/v0"
        
        # Get transactions
        url = f"{base_url}/addresses/{request.address}/transactions"
        params = {
            "api-key": api_key,
            "type": "SWAP",
            "until": f"{request.timeframe}d"
        }
        
        response = requests.get(url, params=params)
        transactions = response.json()
        
        # Safely handle the transactions
        recent_txs = []
        if isinstance(transactions, list):
            recent_txs = transactions[:5] if transactions else []
        
        return {
            "address": request.address,
            "transactions_count": len(recent_txs),
            "recent_transactions": recent_txs
        }
    except Exception as e:
        return {"error": f"Error processing request: {str(e)}"}
