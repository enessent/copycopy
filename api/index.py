from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
from typing import Optional, Dict, List
from datetime import datetime

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

@app.post("/api/analyze")
async def analyze_wallet(request: WalletRequest):
    try:
        api_key = os.environ.get("HELIUS_API_KEY")
        
        # Updated Helius API endpoint
        url = f"https://api.helius.xyz/v1/addresses/{request.address}/transactions"
        
        params = {
            "api-key": api_key,
        }

        print(f"Requesting data for address: {request.address}")  # Debug print
        response = requests.get(url, params=params)
        
        # Debug prints
        print(f"Status code: {response.status_code}")
        print(f"Response text: {response.text[:200]}")  # First 200 chars of response
        
        if response.status_code != 200:
            return {"error": f"Helius API error: {response.status_code}"}
            
        transactions = response.json()
        
        # Basic analysis
        filtered_txs = []
        for tx in transactions:
            if isinstance(tx, dict):  # Verify transaction is valid
                filtered_txs.append({
                    "signature": tx.get("signature", ""),
                    "timestamp": tx.get("timestamp", ""),
                    "type": tx.get("type", ""),
                    "fee": tx.get("fee", 0)
                })
        
        return {
            "address": request.address,
            "timeframe_days": request.timeframe,
            "transactions_count": len(filtered_txs),
            "recent_transactions": filtered_txs[:5],
            "raw_response_sample": str(transactions)[:100] if transactions else "No transactions"  # Debug info
        }
        
    except Exception as e:
        return {"error": f"Error processing request: {str(e)}", "details": str(type(e))}
