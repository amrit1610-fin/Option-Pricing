import numpy as np
from data.market_data import MarketData


class MonteCarloEngine:
    """
    Standard Monte Carlo Simulation for European Options using Geometric Brownian Motion (GBM).
    Optimized with NumPy vectorization for speed.
    """
    def __init__(self, market_data, steps: int = 100, paths: int = 10000):
        self.market_data = market_data
        self.steps = steps
        self.paths = paths

    def _get_payoff(self, final_prices: np.ndarray) -> np.ndarray:
        """Helper to calculate payoff arrays directly from MarketData."""
        K = self.market_data.strike_price
        if self.market_data.option_type.lower() == 'call':
            return np.maximum(final_prices - K, 0.0)
        elif self.market_data.option_type.lower() == 'put':
            return np.maximum(K - final_prices, 0.0)
        else:
            raise ValueError(f"Invalid option type: {self.market_data.option_type}. Must be 'call' or 'put'.")

    def calculate_price(self, **kwargs) -> float:
        """
        Executes the Monte Carlo simulation to price the option.
        """
        # Lock the seed if provided by the Greeks engine
        seed = kwargs.get('seed', None)
        if seed is not None:
            np.random.seed(seed)

        S = self.market_data.spot_price
        T = self.market_data.time_to_expiry
        r = self.market_data.risk_free_rate
        q = self.market_data.dividend_yield
        sigma = self.market_data.volatility
        
        # Edge case: Option is already at expiration
        if T <= 0:
            return float(self._get_payoff(np.array([S]))[0])

        dt = T / self.steps
        
        # Pre-compute drift and diffusion constants for speed
        drift = (r - q - 0.5 * sigma**2) * dt
        diffusion = sigma * np.sqrt(dt)
        
        # Generate random standard normal variables matrix (Paths x Steps)
        Z = np.random.normal(0, 1, (self.paths, self.steps))
        
        # Vectorized path generation
        # Since these are European options, we only need the terminal price.
        # We can sum the log returns across all steps instead of simulating step-by-step.
        log_returns = np.sum(drift + diffusion * Z, axis=1)
        final_prices = S * np.exp(log_returns)
        
        # Calculate terminal payoffs
        payoffs = self._get_payoff(final_prices)
            
        # Discount the average payoff back to present value
        discount_factor = np.exp(-r * T)
        return float(discount_factor * np.mean(payoffs))