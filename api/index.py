from fastapi import FastAPI, HTTPException
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

@app.post("/api/analyze")
async def analyze_wallet(request: WalletRequest):
    try:
        api_key = os.environ.get("HELIUS_API_KEY")
        
        # Helius parseTransactions API endpoint
        url = "https://api.helius.xyz/v0/transactions"
        
        # Get signatures first
        signatures_url = f"https://api.helius.xyz/v0/addresses/{request.address}/transactions"
        signatures_params = {
            "api-key": api_key
        }
        
        # Debug print API key (first few characters)
        print(f"Using API key: {api_key[:5]}..." if api_key else "No API key found")
        
        signatures_response = requests.get(signatures_url, params=signatures_params)
        print(f"Signatures response status: {signatures_response.status_code}")
        
        if signatures_response.status_code != 200:
            return {
                "error": f"Helius API error: {signatures_response.status_code}",
                "details": signatures_response.text
            }
            
        transactions_data = signatures_response.json()
        
        if not transactions_data:
            return {
                "address": request.address,
                "transactions_count": 0,
                "recent_transactions": [],
                "status": "No transactions found"
            }

        return {
            "address": request.address,
            "transactions_count": len(transactions_data),
            "recent_transactions": transactions_data[:5],
            "status": "success"
        }
        
    except Exception as e:
        return {"error": f"Error processing request: {str(e)}"}
