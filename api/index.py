# api/index.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List, Optional
import requests

app = FastAPI()

# CORS configuration for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WalletRequest(BaseModel):
    address: str
    timeframe: Optional[int] = 7

class SolanaAnalyzer:
    def __init__(self):
        self.api_key = os.environ.get("HELIUS_API_KEY")
        if not self.api_key:
            raise ValueError("HELIUS_API_KEY environment variable is not set")
        self.base_url = "https://api.helius.xyz/v0"
    
    def get_transactions(self, address: str, days: int = 7):
        url = f"{self.base_url}/addresses/{address}/transactions"
        params = {
            "api-key": self.api_key,
            "type": "SWAP",
            "until": f"{days}d"
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, 
                              detail="Error fetching transactions from Helius")
        return response.json()

    def analyze_copytrade_patterns(self, transactions):
        patterns = {
            'total_swaps': 0,
            'tokens_traded': set(),
            'dex_interactions': {},
            'timing_patterns': []
        }
        
        for tx in transactions:
            if 'description' in tx:
                patterns['total_swaps'] += 1
                # Add basic pattern analysis
                # You can expand this based on your needs
                
        return patterns

analyzer = SolanaAnalyzer()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/analyze")
async def analyze_wallet(request: WalletRequest):
    try:
        transactions = analyzer.get_transactions(request.address, request.timeframe)
        patterns = analyzer.analyze_copytrade_patterns(transactions)
        
        return {
            "address": request.address,
            "analysis": patterns,
            "recent_transactions": transactions[:10]  # Limit to 10 most recent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))