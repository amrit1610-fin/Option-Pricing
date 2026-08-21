from scipy.optimize import brentq
from typing import Any

class ImpliedVolatility:
    @staticmethod
    def calculate_iv(engine: Any, market_price: float) -> float:
        """
        Backs out IV using the standardized engine and MarketData struct.
        """
        md = engine.md
        original_vol = md.volatility

        def objective_function(sigma: float) -> float:
            md.volatility = sigma
            theoretical_price = engine.calculate_price()
            return theoretical_price - market_price

        try:
            implied_vol = brentq(objective_function, a=1e-4, b=5.0, xtol=1e-5, maxiter=100)
        except ValueError:
            implied_vol = 0.0
            
        # Restore original volatility state
        md.volatility = original_vol
        return implied_vol