import numpy as np
from scipy.stats import norm
from data.market_data import MarketData

class BlackScholesEngine:
    """
    Analytical Black-Scholes-Merton Pricing Engine.
    """
    SUPPORTED_STYLES = ['European']
    SUPPORTED_EXOTICS = ['None']

    def __init__(self, market_data: MarketData):
        self.market_data = market_data

    def calculate_price(self, strike: float, option_type: str = 'call') -> float:
        S = self.market_data.spot_price
        T = self.market_data.time_to_expiry
        r = self.market_data.risk_free_rate
        q = self.market_data.dividend_yield
        sigma = self.market_data.volatility

        if T <= 0:
            return max(S - strike, 0) if option_type == 'call' else max(strike - S, 0)

        d1 = (np.log(S / strike) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type == 'call':
            return S * np.exp(-q * T) * norm.cdf(d1) - strike * np.exp(-r * T) * norm.cdf(d2)
        else:
            return strike * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)

    def calculate_greeks(self, strike: float, option_type: str = 'call') -> dict:
        """Calculates closed-form analytical Greeks."""
        S = self.market_data.spot_price
        T = self.market_data.time_to_expiry
        r = self.market_data.risk_free_rate
        q = self.market_data.dividend_yield
        sigma = self.market_data.volatility

        if T <= 0:
            return {'delta': 0.0, 'gamma': 0.0, 'vega': 0.0, 'theta': 0.0, 'rho': 0.0}

        d1 = (np.log(S / strike) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        delta = np.exp(-q * T) * norm.cdf(d1) if option_type == 'call' else -np.exp(-q * T) * norm.cdf(-d1)
        gamma = (np.exp(-q * T) * norm.pdf(d1)) / (S * sigma * np.sqrt(T))
        vega = (S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T)) / 100

        term1 = -(S * np.exp(-q * T) * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        if option_type == 'call':
            theta = (term1 - r * strike * np.exp(-r * T) * norm.cdf(d2) + q * S * np.exp(-q * T) * norm.cdf(d1)) / 365
            rho = (strike * T * np.exp(-r * T) * norm.cdf(d2)) / 100
        else:
            theta = (term1 + r * strike * np.exp(-r * T) * norm.cdf(-d2) - q * S * np.exp(-q * T) * norm.cdf(-d1)) / 365
            rho = (-strike * T * np.exp(-r * T) * norm.cdf(-d2)) / 100

        return {'delta': delta, 'gamma': gamma, 'vega': vega, 'theta': theta, 'rho': rho}