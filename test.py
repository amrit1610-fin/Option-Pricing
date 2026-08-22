from data.market_data import MarketData
from models.black_scholes import BlackScholesEngine
from models.binomial_tree import BinomialTreeEngine
from models.monte_carlo import MonteCarloEngine
from models.heston import HestonFourierEngine, HestonMonteCarloEngine
import copy
from utils.implied_vol import ImpliedVolatility
from utils.greeks import NumericalGreeks

ticker = "^SPX"
expiry = "2026-08-28"
strike = 7700.00
option = "Put"

data = MarketData()
fetched_data = data.get_market_data(ticker, expiry, strike, option)

print("=======Contract Details=======")
print("Spot price: ",fetched_data.spot_price)
print("Strike price: ",fetched_data.strike_price)
print("Risk-free rate: ",fetched_data.risk_free_rate)
print("Time to expiry: ",fetched_data.time_to_expiry)
print("Option type: ",fetched_data.option_type)
print("Exercise Style: ",fetched_data.exercise_style)
print("Dividend yield: ",fetched_data.dividend_yield)
print("Volatility: ",fetched_data.volatility)
print("Market price: ",fetched_data.market_price)
print("="*20)

print("=======Model Training=======")
models = []
if fetched_data.exercise_style == 'american':
    models = [BlackScholesEngine, BinomialTreeEngine]
else:
    models = [BlackScholesEngine, BinomialTreeEngine, MonteCarloEngine, HestonFourierEngine, HestonMonteCarloEngine]

v0 = 0.04
rho = -0.7
kappa = 2
theta = 0.04
sigma_v = 0.03


for model_class in models:
    print(f"\n--- Running {model_class.__name__} ---")
    
    # 1. Isolate the data state so models don't contaminate each other
    md_current = copy.deepcopy(fetched_data)
    
    if model_class in (BlackScholesEngine, BinomialTreeEngine, MonteCarloEngine):
        engine = model_class(md_current)
        
        # Flag to tell the wrappers to lock the random seed
        is_mc = (model_class == MonteCarloEngine)
        
        # 2. Calculate Implied Volatility using the OPTION'S market price
        true_iv = ImpliedVolatility.calculate_iv(
            engine=engine, 
            market_price=md_current.market_price, 
            is_monte_carlo=is_mc
        )
        print(f"Calculated True IV: {true_iv:.2%}")
        
        # 3. Overwrite the fallback volatility with the True IV
        md_current.volatility = true_iv
        
        # 4. Calculate Price AND Greeks simultaneously
        results = NumericalGreeks.calculate_greeks(engine=engine, is_monte_carlo=is_mc)
        
        print(f"Price: ${results['price']:.4f}")
        print(f"Delta: {results['delta']:.4f} | Gamma: {results['gamma']:.4f}")
        print(f"Theta: {results['theta']:.4f} | Vega: {results['vega']:.4f}")
        
    else:
        # Heston Models (No IV input, relies on stochastic parameters)
        engine = model_class(md_current, v0, rho, kappa, theta, sigma_v)
        
        is_heston_mc = (model_class == HestonMonteCarloEngine)
        
        # Calculate Price AND Greeks (NumericalGreeks works on Heston too!)
        results = NumericalGreeks.calculate_greeks(engine=engine, is_monte_carlo=is_heston_mc)
        
        print(f"Price: ${results['price']:.4f}")
        print(f"Delta: {results['delta']:.4f} | Gamma: {results['gamma']:.4f}")
        print(f"Theta: {results['theta']:.4f}")
        # Note: Vega requires bumping v0 or sigma_v in Heston, so standard Vega might return 0.0 here.