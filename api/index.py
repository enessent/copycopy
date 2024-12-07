from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
from typing import Optional, List, Dict
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

@app.post("/api/analyze")
async def analyze_wallet(request: WalletRequest):
    try:
        api_key = os.environ.get("HELIUS_API_KEY")
        
        # Get transactions
        signatures_url = f"https://api.helius.xyz/v0/addresses/{request.address}/transactions"
        params = {
            "api-key": api_key
        }
        
        response = requests.get(signatures_url, params=params)
        
        if response.status_code != 200:
            return {
                "error": f"Helius API error: {response.status_code}",
                "details": response.text
            }
            
        transactions = response.json()
        
        # Analyze transactions
        analysis = analyze_transactions(transactions)
        
        return {
            "address": request.address,
            "analysis": analysis,
            "recent_transactions": transactions[:5],
            "status": "success"
        }
        
    except Exception as e:
        return {"error": f"Error processing request: {str(e)}"}

def analyze_transactions(transactions: List[Dict]) -> Dict:
    """Analyze transactions for copytrading patterns"""
    
    analysis = {
        "transaction_count": len(transactions),
        "trading_patterns": {
            "total_swaps": 0,
            "unique_tokens": set(),
            "time_distribution": {},
            "potential_copy_trades": []
        },
        "timing_analysis": {
            "average_time_between_trades": 0,
            "most_active_hours": [],
            "trade_frequency_by_day": {}
        }
    }
    
    if not transactions:
        return analysis
    
    # Process transactions
    timestamps = []
    for tx in transactions:
        if "timestamp" in tx:
            dt = datetime.fromtimestamp(tx["timestamp"])
            timestamps.append(dt)
            
            # Track time distribution
            hour = dt.hour
            analysis["trading_patterns"]["time_distribution"][hour] = \
                analysis["trading_patterns"]["time_distribution"].get(hour, 0) + 1
            
            # Track daily frequency
            day = dt.strftime("%Y-%m-%d")
            analysis["timing_analysis"]["trade_frequency_by_day"][day] = \
                analysis["timing_analysis"]["trade_frequency_by_day"].get(day, 0) + 1
    
    # Calculate time between trades
    if len(timestamps) > 1:
        timestamps.sort()
        time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() 
                     for i in range(len(timestamps)-1)]
        avg_time = sum(time_diffs) / len(time_diffs) if time_diffs else 0
        analysis["timing_analysis"]["average_time_between_trades"] = round(avg_time / 60, 2)  # in minutes
    
    # Find most active hours
    if analysis["trading_patterns"]["time_distribution"]:
        sorted_hours = sorted(
            analysis["trading_patterns"]["time_distribution"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        analysis["timing_analysis"]["most_active_hours"] = [hour for hour, _ in sorted_hours[:5]]
    
    # Look for potential copy trades (transactions close in time)
    if len(timestamps) > 1:
        for i in range(len(timestamps)-1):
            time_diff = (timestamps[i+1] - timestamps[i]).total_seconds()
            if time_diff <= 60:  # Transactions within 1 minute
                analysis["trading_patterns"]["potential_copy_trades"].append({
                    "tx1_time": timestamps[i].isoformat(),
                    "tx2_time": timestamps[i+1].isoformat(),
                    "time_difference_seconds": time_diff
                })
    
    return analysis
