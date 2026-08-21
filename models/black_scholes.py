import numpy as np
from scipy.stats import norm

class BlackScholesEngine:
    """
    Analytical Black-Scholes-Merton Pricing Engine.
    """

    def __init__(self, market_data):
        self.market_data = market_data

    def calculate_price(self) -> float:
        S = self.market_data.spot_price
        K = self.market_data.strike_price
        T = self.market_data.time_to_expiry
        r = self.market_data.risk_free_rate
        q = self.market_data.dividend_yield
        sigma = self.market_data.volatility
        option_type = self.market_data.option_type

        if T <= 0:
            return max(S - K, 0) if option_type.lower() == 'call' else max(K - S, 0)

        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type.lower() == 'call':
            return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:
            return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)

    def calculate_greeks(self) -> dict:
        """Calculates closed-form analytical Greeks."""
        S = self.market_data.spot_price
        K = self.market_data.strike_price
        T = self.market_data.time_to_expiry
        r = self.market_data.risk_free_rate
        q = self.market_data.dividend_yield
        sigma = self.market_data.volatility
        option_type = self.market_data.option_type

        if T <= 0:
            return {'delta': 0.0, 'gamma': 0.0, 'vega': 0.0, 'theta': 0.0, 'rho': 0.0}

        d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        delta = np.exp(-q * T) * norm.cdf(d1) if option_type == 'call' else -np.exp(-q * T) * norm.cdf(-d1)
        gamma = (np.exp(-q * T) * norm.pdf(d1)) / (S * sigma * np.sqrt(T))
        vega = (S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T)) / 100

        term1 = -(S * np.exp(-q * T) * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        if option_type.lower() == 'call':
            theta = (term1 - r * K * np.exp(-r * T) * norm.cdf(d2) + q * S * np.exp(-q * T) * norm.cdf(d1)) / 365
            rho = (K * T * np.exp(-r * T) * norm.cdf(d2)) / 100
        else:
            theta = (term1 + r * K * np.exp(-r * T) * norm.cdf(-d2) - q * S * np.exp(-q * T) * norm.cdf(-d1)) / 365
            rho = (-K * T * np.exp(-r * T) * norm.cdf(-d2)) / 100

        return {'delta': delta, 
                'gamma': gamma, 
                'vega': vega, 
                'theta': theta, 
                'rho': rho
                }