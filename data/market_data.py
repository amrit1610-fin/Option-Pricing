import requests
from datetime import datetime
from data.market_data_layout import MarketDataLayout

class MarketData:
    def __init__(self):
        self.base_url = "https://api.marketdata.app/v1/options/quotes"

    def _generate_occ_symbol(self, ticker: str, expiration_date: str, strike_price: float, option_type: str) -> str:
        """Constructs standard OCC symbol: e.g., SPXW260828P05500000"""
        clean_ticker = ticker.upper().replace("^", "")
        ticker_padded = clean_ticker.ljust(6)
        
        exp_date_obj = datetime.strptime(expiration_date, "%Y-%m-%d")
        date_str = exp_date_obj.strftime("%y%m%d")
        call_put = 'C' if option_type.lower() == 'call' else 'P'
        strike_str = f"{int(strike_price * 1000):08d}"
        
        return f"{ticker_padded}{date_str}{call_put}{strike_str}"

    def get_market_data(self, ticker: str, expiration_date: str, strike_price: float, option_type: str) -> MarketDataLayout:
        clean_ticker = ticker.upper().replace("^", "")
        occ_symbol = self._generate_occ_symbol(clean_ticker, expiration_date, strike_price, option_type)
        
        try:
            # Hit the MarketData API (No key required for <100 requests/day)
            url = f"{self.base_url}/{occ_symbol}/"
            response = requests.get(url)
            
            if response.status_code == 429:
                raise ValueError("MarketData API Free Daily Limit Hit (100 requests).")
            elif response.status_code != 200:
                raise ValueError(f"Could not fetch data for {occ_symbol}. Contract may not exist.")
            
            data = response.json()
            
            if data.get("s") != "ok":
                raise ValueError("Invalid contract parameters or expired option.")

            # Extract pricing data
            spot_price = float(data.get("underlyingPrice", [0])[0])
            bid = float(data.get("bid", [0])[0])
            ask = float(data.get("ask", [0])[0])
            market_price = (bid + ask) / 2.0 if bid and ask else (bid or ask or 0.0)
            
            # API provides IV, but we let our backend recalculate it for precision
            volatility = 0.20 

            # Time to Expiry
            exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
            days_to_expiry = (exp_date - datetime.now()).days
            time_to_expiry = max(days_to_expiry / 365.0, 0.001)

            # Exercise Style
            european_indices = ["SPX", "SPXW", "XSP", "NDX", "RUT", "VIX"]
            exercise_style = "european" if clean_ticker in european_indices else "american"

            return MarketDataLayout(
                spot_price=spot_price,
                strike_price=strike_price,
                risk_free_rate=0.05,
                time_to_expiry=time_to_expiry,
                option_type=option_type.lower(),
                exercise_style=exercise_style,
                dividend_yield=0.0,
                volatility=volatility,
                market_price=market_price
            )
            
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise ValueError(f"MarketData API Error: {str(e)}")