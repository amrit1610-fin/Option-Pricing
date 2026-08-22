from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import math
import numpy as np
import copy

from data.market_data import MarketData
from models.black_scholes import BlackScholesEngine
from models.binomial_tree import BinomialTreeEngine
from models.monte_carlo import MonteCarloEngine
from utils.implied_vol import ImpliedVolatility
from utils.greeks import NumericalGreeks

app = FastAPI(title="Option Pricing Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PricingRequest(BaseModel):
    ticker: str
    expiration_date: str
    strike_price: float
    option_type: str
    # Removed model_name!

def safe_float(val):
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return 0.0
    return val

def generate_chart_data(md, base_iv, is_european):
    vis_data = {
        "strikes": [],
        "deltas": [],
        "convergence_steps": [10, 50, 100, 150, 200],
        "binomial_prices": [],
        "mc_paths": []
    }
    
    # 1. Delta vs Strike (Using Black-Scholes math for the curve)
    for mult in [0.8, 0.9, 1.0, 1.1, 1.2]:
        temp_md = copy.deepcopy(md)
        temp_md.strike_price = md.strike_price * mult
        temp_md.volatility = base_iv # Use stable IV
        temp_bs = BlackScholesEngine(temp_md)
        greeks = NumericalGreeks.calculate_greeks(temp_bs, is_monte_carlo=False)
        vis_data["strikes"].append(safe_float(temp_md.strike_price))
        vis_data["deltas"].append(safe_float(greeks.get("delta", 0.0)))

    # 2. Binomial Convergence Array
    for n in vis_data["convergence_steps"]:
        temp_tree = BinomialTreeEngine(copy.deepcopy(md), N=n)
        vis_data["binomial_prices"].append(safe_float(temp_tree.calculate_price()))

    # 3. Monte Carlo Price Paths (10 sample paths, 100 time steps)
    if md.spot_price > 0 and md.time_to_expiry > 0:
        dt = md.time_to_expiry / 100
        for _ in range(10):
            path = [md.spot_price]
            for _ in range(100):
                z = np.random.normal()
                # Standard Geometric Brownian Motion
                drift = (md.risk_free_rate - 0.5 * base_iv**2) * dt
                shock = base_iv * np.sqrt(dt) * z
                path.append(path[-1] * np.exp(drift + shock))
            vis_data["mc_paths"].append(path)

    return vis_data


@app.post("/api/price")
def price_option(req: PricingRequest):
    try:
        data = MarketData()
        md = data.get_market_data(
            ticker=req.ticker, 
            expiration_date=req.expiration_date, 
            strike_price=req.strike_price, 
            option_type=req.option_type
        )
        
        if md.spot_price is None or md.spot_price <= 0:
            raise HTTPException(status_code=404, detail=f"Invalid ticker or no data for '{req.ticker}'.")

        # Get stable BS IV to parameterize models safely
        if md.market_price and md.market_price > 0:
            bs_temp = BlackScholesEngine(md)
            stable_iv = ImpliedVolatility.calculate_iv(bs_temp, md.market_price, False)
            md.volatility = stable_iv

        # --- AUTO-ROUTING LOGIC ---
        valid_models = {}
        style = md.exercise_style.lower()
        
        if style == 'american':
            # American options can only use trees
            valid_models['BINOMIAL TREE'] = BinomialTreeEngine(copy.deepcopy(md), N=200)
        else:
            # European options can use all three
            valid_models['BLACK-SCHOLES'] = BlackScholesEngine(copy.deepcopy(md))
            valid_models['BINOMIAL TREE'] = BinomialTreeEngine(copy.deepcopy(md), N=200)
            valid_models['MONTE CARLO'] = MonteCarloEngine(copy.deepcopy(md))

        # Calculate results for all valid models
        all_results = {}
        for name, engine in valid_models.items():
            is_mc = (name == 'MONTE CARLO')
            raw = NumericalGreeks.calculate_greeks(engine, is_mc)
            all_results[name] = {k: safe_float(v) for k, v in raw.items()}
        
        # Generate plotting arrays
        chart_data = generate_chart_data(
            md=md, 
            base_iv=stable_iv, 
            is_european=(style != 'american')
        )
        

        return {
            "status": "success",
            "contract_details": {
                "spot_price": safe_float(md.spot_price),
                "strike_price": safe_float(md.strike_price),
                "risk_free_rate": safe_float(md.risk_free_rate),
                "time_to_expiry": safe_float(md.time_to_expiry),
                "implied_volatility": safe_float(md.volatility),
                "market_price": safe_float(md.market_price),
                "exercise_style": md.exercise_style.upper()
            },
            "results": all_results,
            "charts": chart_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))