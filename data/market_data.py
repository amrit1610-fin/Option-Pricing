from dataclasses import dataclass
from typing import Optional

@dataclass
class MarketData:
    """
    Object-Oriented data container for market variables.
    This acts as the standardized 'plate' of data that is fed into the pricing engines.
    Because it is decoupled from the live API, it can be easily modified in-memory 
    for calculating Greeks via finite difference (bump-and-revalue).
    """
    spot_price: float
    strike_price: float               
    risk_free_rate: float
    time_to_expiry: float             # Represented in years (e.g., 0.5 for 6 months)
    option_type: str                  # 'call' or 'put'
    exercise_style: str               # 'european' or 'american'
    dividend_yield: float = 0.0       # Default to 0.0 if not provided
    volatility: Optional[float] = None # Optional: Used for Black-Scholes, unused in Heston