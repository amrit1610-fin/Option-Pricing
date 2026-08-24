import numpy as np
import copy
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import math

from data.market_data import MarketData
from models.black_scholes import BlackScholesEngine
from models.binomial_tree import BinomialTreeEngine
from models.monte_carlo import MonteCarloEngine
from utils.implied_vol import ImpliedVolatility
from utils.greeks import NumericalGreeks

app = FastAPI(title="Option Pricing Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # The wildcard '*' allows requests from any domain (Vercel & Localhost)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PricingRequest(BaseModel):
    ticker: str
    expiration_date: str
    strike_price: float
    option_type: str

def safe_float(val):
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return 0.0
    return val

# --- VISUALIZATION GENERATOR ---
def generate_chart_data(md, base_iv, is_european):
    vis_data = {
        "payoff_spots": [],
        "payoffs": [],
        "strikes": [],
        "deltas": [],
        "gammas": [],
        "thetas": [],
        "vegas": [],
        "rhos": [],
        "convergence_steps": list(range(10, 100, 2)), 
        "binomial_prices": [],
        "mc_sim_counts": [100, 500, 1000, 2500, 5000, 10000],
        "mc_prices": [],
        "mc_lower": [],
        "mc_upper": [],
        "bs_price": 0.0,
        "mc_paths": []
    }
    
    # Baseline BS Price
    baseline_bs = BlackScholesEngine(copy.deepcopy(md))
    vis_data["bs_price"] = safe_float(baseline_bs.calculate_price())

    # 0. True Payoff Curve (Underlying Spot vs Payoff)
    spot_range = np.linspace(md.strike_price * 0.7, md.strike_price * 1.3, 50)
    vis_data["payoff_spots"] = [safe_float(s) for s in spot_range]
    for s in spot_range:
        if md.option_type.lower() == 'call':
            vis_data["payoffs"].append(safe_float(max(s - md.strike_price, 0)))
        else:
            vis_data["payoffs"].append(safe_float(max(md.strike_price - s, 0)))

    # 1. Greeks vs Strike (And ITM Probability)
    strike_multipliers = np.linspace(0.8, 1.2, 20)
    for mult in strike_multipliers:
        temp_md = copy.deepcopy(md)
        temp_md.strike_price = md.strike_price * mult
        temp_md.volatility = base_iv
        temp_bs = BlackScholesEngine(temp_md)
        greeks = NumericalGreeks.calculate_greeks(temp_bs, is_monte_carlo=False)
        
        vis_data["strikes"].append(safe_float(temp_md.strike_price))
        vis_data["deltas"].append(safe_float(greeks.get("delta", 0.0)))
        vis_data["gammas"].append(safe_float(greeks.get("gamma", 0.0)))
        vis_data["thetas"].append(safe_float(greeks.get("theta", 0.0)))
        vis_data["vegas"].append(safe_float(greeks.get("vega", 0.0)))
        vis_data["rhos"].append(safe_float(greeks.get("rho", 0.0)))

    # 2. Binomial Convergence
    for n in vis_data["convergence_steps"]:
        temp_tree = BinomialTreeEngine(copy.deepcopy(md), N=n)
        vis_data["binomial_prices"].append(safe_float(temp_tree.calculate_price()))

    # 3. Monte Carlo Paths & Convergence
    if md.spot_price > 0 and md.time_to_expiry > 0:
        dt = md.time_to_expiry / 100
        drift = (md.risk_free_rate - 0.5 * base_iv**2) * dt
        vol_sqrt_dt = base_iv * np.sqrt(dt)
        
        for _ in range(50):
            path = [md.spot_price]
            for _ in range(100):
                z = np.random.normal()
                path.append(path[-1] * np.exp(drift + vol_sqrt_dt * z))
            vis_data["mc_paths"].append(path)
            
        for sims in vis_data["mc_sim_counts"]:
            z_mat = np.random.normal(size=(sims, 100))
            paths_end = md.spot_price * np.exp(np.sum(drift + vol_sqrt_dt * z_mat, axis=1))
            if md.option_type.lower() == 'call':
                payoffs = np.maximum(paths_end - md.strike_price, 0)
            else:
                payoffs = np.maximum(md.strike_price - paths_end, 0)
            
            discounted = payoffs * np.exp(-md.risk_free_rate * md.time_to_expiry)
            mean_p = float(np.mean(discounted))
            std_err = float(np.std(discounted) / np.sqrt(sims))
            
            vis_data["mc_prices"].append(safe_float(mean_p))
            vis_data["mc_lower"].append(safe_float(mean_p - 1.96 * std_err)) 
            vis_data["mc_upper"].append(safe_float(mean_p + 1.96 * std_err)) 

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

        if md.market_price and md.market_price > 0:
            bs_temp = BlackScholesEngine(md)
            stable_iv = ImpliedVolatility.calculate_iv(bs_temp, md.market_price, False)
            md.volatility = stable_iv
        else:
            stable_iv = md.volatility

        valid_models = {}
        style = md.exercise_style.lower()
        
        if style == 'american':
            valid_models['BINOMIAL TREE'] = BinomialTreeEngine(copy.deepcopy(md), N=200)
        else:
            valid_models['BLACK-SCHOLES'] = BlackScholesEngine(copy.deepcopy(md))
            valid_models['BINOMIAL TREE'] = BinomialTreeEngine(copy.deepcopy(md), N=200)
            valid_models['MONTE CARLO'] = MonteCarloEngine(copy.deepcopy(md))

        all_results = {}
        for name, engine in valid_models.items():
            is_mc = (name == 'MONTE CARLO')
            raw = NumericalGreeks.calculate_greeks(engine, is_mc)
            all_results[name] = {k: safe_float(v) for k, v in raw.items()}
        
        chart_data = generate_chart_data(md, stable_iv, style != 'american')
        
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