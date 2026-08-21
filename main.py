import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from datetime import datetime
from data.market_data import MarketData
from utils.greeks import NumericalGreeks
from models.black_scholes import BlackScholesEngine
from models.binomial_tree import BinomialTreeEngine
from models.monte_carlo import MonteCarloEngine
from models.heston import HestonFourierEngine, HestonMonteCarloEngine


# Initialize the FastAPI app
app = FastAPI(title="Option Pricing API", version="1.0")

# CRITICAL: Configure CORS (Cross-Origin Resource Sharing)
# This allows your Node.js/React frontend (which will run on a different port) 
# to securely request data from this Python backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this would be your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request Models (Pydantic) ---
class ChainRequest(BaseModel):
    ticker: str
    expiry_date: str

class PricingRequest(BaseModel):
    ticker: str
    expiry_date: str
    strike: float
    option_type: str = "call"  # "call" or "put"
    model_name: str = "black_scholes"  # "black_scholes", "binomial", "monte_carlo", "heston"

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"status": "Option Pricing API is running live."}

@app.get("/api/market-info/{ticker}")
def get_market_info(ticker: str):
    """
    Fetches the spot price, risk-free rate, and available expirations for a ticker.
    """
    spot = MarketData.get_spot_price(ticker)
    if spot is None:
        raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}")

    r = MarketData.get_risk_free_rate()
    expirations = MarketData.get_expirations(ticker)

    return {
        "ticker": ticker.upper(),
        "spot_price": spot,
        "risk_free_rate": r,
        "expirations": expirations
    }

@app.post("/api/option-chain")
def get_option_chain(request: ChainRequest):
    """
    Fetches the full calls and puts dataframe for a specific ticker and expiration.
    """
    chain = MarketData.get_option_chain(request.ticker, request.expiry_date)
    
    if chain is None:
        raise HTTPException(status_code=404, detail="Option chain not found or invalid expiry.")

    # We must convert Pandas DataFrames to dictionaries so FastAPI can send them as JSON to React
    # orient="records" creates a clean list of JSON objects (perfect for React tables)
    calls_json = chain["calls"].to_dict(orient="records")
    puts_json = chain["puts"].to_dict(orient="records")

    return {
        "calls": calls_json,
        "puts": puts_json
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)