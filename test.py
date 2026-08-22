import copy
from data.market_data import MarketData
from models.black_scholes import BlackScholesEngine
from models.binomial_tree import BinomialTreeEngine
from models.monte_carlo import MonteCarloEngine
from utils.implied_vol import ImpliedVolatility
from utils.greeks import NumericalGreeks

# --- 1. Define Option Parameters ---
ticker = "^SPX"
expiry = "2026-08-28"
strike = 7700.00
option = "Put"

# --- 2. Fetch Market Data ---
data = MarketData()
# Note: Ensure your MarketData class logic correctly binds to this fetch method
fetched_data = data.get_market_data(ticker, expiry, strike, option)

print("======= Contract Details =======")
print(f"Spot price:     {fetched_data.spot_price}")
print(f"Strike price:   {fetched_data.strike_price}")
print(f"Risk-free rate: {fetched_data.risk_free_rate}")
print(f"Time to expiry: {fetched_data.time_to_expiry}")
print(f"Option type:    {fetched_data.option_type}")
print(f"Exercise Style: {fetched_data.exercise_style}")
print(f"Dividend yield: {fetched_data.dividend_yield}")
print(f"Volatility:     {fetched_data.volatility}")
print(f"Market price:   {fetched_data.market_price}")
print("================================")

# --- 3. Determine Eligible Models ---
print("\n======= Model Evaluation =======")
if fetched_data.exercise_style.lower() == 'american':
    # Monte Carlo (without LSM) only supports European options
    models = [BlackScholesEngine, BinomialTreeEngine]
else:
    models = [BlackScholesEngine, BinomialTreeEngine, MonteCarloEngine]

# --- 4. Run Pricing & Greeks Engine ---
for model_class in models:
    print(f"\n--- Running {model_class.__name__} ---")
    
    # Isolate the data state so models do not contaminate each other's IV
    md_current = copy.deepcopy(fetched_data)
    engine = model_class(md_current)
    
    # Flag to tell the wrappers to lock the random seed for finite difference
    is_mc = (model_class == MonteCarloEngine)
    
    # Calculate Implied Volatility (if a valid market price exists)
    if md_current.market_price and md_current.market_price > 0:
        true_iv = ImpliedVolatility.calculate_iv(
            engine=engine, 
            market_price=md_current.market_price, 
            is_monte_carlo=is_mc
        )
        print(f"Calculated True IV: {true_iv:.2%}")
        
        # Overwrite the fallback volatility with the True IV for accurate Greeks
        md_current.volatility = true_iv
    else:
        print("Notice: No valid market price found. Using fallback IV.")
    
    # Calculate Price AND Greeks simultaneously
    results = NumericalGreeks.calculate_greeks(engine=engine, is_monte_carlo=is_mc)
    
    # Display Results
    print(f"Theoretical Price: ${results['price']:.4f}")
    print(f"Delta: {results['delta']:.4f} | Gamma: {results['gamma']:.4f}")
    print(f"Theta: {results['theta']:.4f} | Vega:  {results['vega']:.4f}")
    print(f"Rho:   {results['rho']:.4f}")