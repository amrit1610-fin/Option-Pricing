import numpy as np
from data.market_data import MarketData

class MonteCarloEngine:
    """
    Standard Monte Carlo Simulation for European Options using Geometric Brownian Motion.
    SDE: $dS_t = r S_t dt + \sigma S_t dW_t$
    """
    def __init__(self, market_data: MarketData, steps: int = 100, paths: int = 10000):
        self.md = market_data
        self.steps = steps
        self.paths = paths

    def calculate_price(self, seed: int = None) -> float:
        if seed is not None:
            np.random.seed(seed)

        dt = self.md.time_to_expiry / self.steps
        
        # Pre-compute drift and diffusion
        drift = (self.md.risk_free_rate - self.md.dividend_yield - 0.5 * self.md.volatility**2) * dt
        diffusion = self.md.volatility * np.sqrt(dt)
        
        # Generate random paths
        Z = np.random.normal(0, 1, (self.paths, self.steps))
        
        # Vectorized path generation
        S_T = self.md.spot_price * np.exp(np.sum(drift + diffusion * Z, axis=1))
        
        # Calculate payoff
        if self.md.option_type == 'call':
            payoff = np.maximum(S_T - self.md.strike_price, 0)
        elif self.md.option_type == 'put':
            payoff = np.maximum(self.md.strike_price - S_T, 0)
        else:
            raise ValueError("Invalid option type.")
            
        # Discount to present value
        return float(np.exp(-self.md.risk_free_rate * self.md.time_to_expiry) * np.mean(payoff))