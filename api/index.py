from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
from typing import Optional, Dict, List
from datetime import datetime, timedelta

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
    min_amount: Optional[float] = 0.1  # Minimum SOL amount to consider

class TransactionAnalysis:
    def __init__(self, transactions: List[Dict]):
        self.transactions = transactions
        
    def analyze_trading_patterns(self) -> Dict:
        if not self.transactions:
            return {
                "total_swaps": 0,
                "tokens_traded": [],
                "most_traded_tokens": [],
                "avg_time_between_trades": 0,
                "active_hours": [],
                "largest_trade": 0
            }
            
        tokens = {}
        timestamps = []
        largest_trade = 0
        
        for tx in self.transactions:
            # Extract token info and amounts
            if "tokenTransfers" in tx:
                for transfer in tx["tokenTransfers"]:
                    token_address = transfer.get("mint", "unknown")
                    tokens[token_address] = tokens.get(token_address, 0) + 1
                    
            # Track timestamps for pattern analysis
            if "timestamp" in tx:
                timestamps.append(datetime.fromtimestamp(tx["timestamp"]))
                
            # Track largest trade
            if "nativeTransfers" in tx:
                for transfer in tx["nativeTransfers"]:
                    amount = float(transfer.get("amount", 0)) / 1e9  # Convert lamports to SOL
                    largest_trade = max(largest_trade, amount)
        
        # Calculate time between trades
        avg_time_between = 0
        if len(timestamps) > 1:
            timestamps.sort()
            time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                         for i in range(len(timestamps)-1)]
            avg_time_between = sum(time_diffs) / len(time_diffs)
        
        # Calculate active hours
        active_hours = []
        if timestamps:
            hours = [ts.hour for ts in timestamps]
            active_hours = sorted(set(hours))
        
        # Sort tokens by frequency
        most_traded = sorted(tokens.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_swaps": len(self.transactions),
            "tokens_traded": list(tokens.keys()),
            "most_traded_tokens": most_traded,
            "avg_time_between_trades": round(avg_time_between / 60, 2),  # in minutes
            "active_hours": active_hours,
            "largest_trade": round(largest_trade, 3)
        }

@app.post("/api/analyze")
async def analyze_wallet(request: WalletRequest):
    try:
        api_key = os.environ.get("HELIUS_API_KEY")
        base_url = "https://api.helius.xyz/v0"
        
        url = f"{base_url}/addresses/{request.address}/transactions"
        params = {
            "api-key": api_key,
            "type": "SWAP",
            "until": f"{request.timeframe}d"
        }
        
        response = requests.get(url, params=params)
        transactions = response.json()
        
        if not isinstance(transactions, list):
            return {"error": "Invalid response from Helius API"}
            
        analyzer = TransactionAnalysis(transactions)
        analysis = analyzer.analyze_trading_patterns()
        
        return {
            "address": request.address,
            "timeframe_days": request.timeframe,
            "analysis": analysis,
            "recent_transactions": transactions[:5] if transactions else []
        }
        
    except Exception as e:
        return {"error": f"Error processing request: {str(e)}"}
