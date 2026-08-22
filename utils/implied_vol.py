from scipy.optimize import brentq
from typing import Any

class ImpliedVolatility:
    """
    Universal Implied Volatility calculator. 
    Works with any PricingEngine that uses the MarketData struct.
    """
    
    @staticmethod
    def calculate_iv(engine: Any, market_price: float, is_monte_carlo: bool = False) -> float:
        md = engine.market_data
        original_vol = md.volatility  # Save the original state

        # Seed is required for Monte Carlo so the root-finder doesn't get confused by random noise
        kwargs = {"seed": 42} if is_monte_carlo else {}

        def objective_function(sigma: float) -> float:
            md.volatility = sigma  # Temporarily inject new volatility
            theoretical_price = engine.calculate_price(**kwargs)
            return theoretical_price - market_price

        try:
            implied_vol = brentq(objective_function, a=1e-4, b=5.0, xtol=1e-5, maxiter=100)
        except ValueError:
            # FIX: Return a tiny non-zero number instead of 0.0 to prevent division by zero
            implied_vol = 1e-4
            
        # Restore the engine to its original state so we don't cause side effects
        md.volatility = original_vol 
        
        return implied_vol