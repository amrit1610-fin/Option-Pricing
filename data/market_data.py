import os
import requests
from datetime import datetime
from typing import Optional

from data.market_data_layout import MarketDataLayout

class MarketData:
    def __init__(self):
        # Load API credentials from environment variables
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.headers = {
            "APCA-API-KEY-ID": self.api_key or "",
            "APCA-API-SECRET-KEY": self.secret_key or "",
            "Accept": "application/json"
        }
        self.base_url = "https://data.alpaca.markets"

    def _generate_occ_symbol(self, ticker: str, expiration_date: str, strike_price: float, option_type: str) -> str:
        """Constructs standard OCC symbol: [Ticker 6-char][YYMMDD][C/P][Strike*1000 8-digit]"""
        clean_ticker = ticker.upper().replace("^", "")
        ticker_padded = clean_ticker.ljust(6)
        
        exp_date_obj = datetime.strptime(expiration_date, "%Y-%m-%d")
        date_str = exp_date_obj.strftime("%y%m%d")
        call_put = 'C' if option_type.lower() == 'call' else 'P'
        strike_str = f"{int(strike_price * 1000):08d}"
        
        return f"{ticker_padded}{date_str}{call_put}{strike_str}"

    def get_market_data(self, ticker: str, expiration_date: str, strike_price: float, option_type: str) -> MarketDataLayout:
        if not self.api_key or not self.secret_key:
            raise ValueError("SYSTEM ERROR: Alpaca API Keys (ALPACA_API_KEY, ALPACA_SECRET_KEY) are missing in Render environment variables.")

        clean_ticker = ticker.upper().replace("^", "")
        equity_proxy = "SPY" if clean_ticker == "SPX" else "QQQ" if clean_ticker == "NDX" else clean_ticker

        try:
            # 1. Underlying Spot Price
            spot_url = f"{self.base_url}/v2/stocks/{equity_proxy}/trades/latest"
            spot_res = requests.get(spot_url, headers=self.headers)
            
            if spot_res.status_code == 401:
                raise ValueError("Alpaca API Keys are invalid. Check Render Environment Variables.")
            elif spot_res.status_code == 429:
                raise ValueError("Alpaca API Rate Limit Hit. Please wait a moment.")
            
            spot_data = spot_res.json()
            if "trade" not in spot_data:
                raise ValueError(f"Could not fetch spot price for {equity_proxy}.")
            
            spot_price = float(spot_data["trade"]["p"])
            if clean_ticker == "SPX": 
                spot_price *= 10.0

            # 2. Risk-Free Rate
            risk_free_rate = 0.05

            # 3. Options Data & Mid-Price
            occ_symbol = self._generate_occ_symbol(clean_ticker, expiration_date, strike_price, option_type)
            opt_url = f"{self.base_url}/v1beta1/options/quotes/latest?symbols={occ_symbol}"
            opt_res = requests.get(opt_url, headers=self.headers)
            
            market_price = 0.0
            volatility = 0.20  # Base initial estimate; IV solver refines this
            
            if opt_res.status_code == 200:
                opt_data = opt_res.json()
                if "quotes" in opt_data and occ_symbol in opt_data["quotes"]:
                    quote = opt_data["quotes"][occ_symbol]
                    bid = float(quote.get("bp", 0.0))
                    ask = float(quote.get("ap", 0.0))
                    
                    if bid > 0 and ask > 0:
                        market_price = (bid + ask) / 2.0
                    elif bid > 0 or ask > 0:
                        market_price = bid if bid > 0 else ask

            # 4. Time to Expiry
            exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
            days_to_expiry = (exp_date - datetime.now()).days
            time_to_expiry = max(days_to_expiry / 365.0, 0.001)

            # 5. Exercise Style
            european_indices = ["SPX", "SPXW", "XSP", "NDX", "RUT", "VIX", "DJX", "XEO", "MNX"]
            exercise_style = "european" if clean_ticker in european_indices else "american"

            # 6. Return standard MarketDataLayout
            return MarketDataLayout(
                spot_price=spot_price,
                strike_price=strike_price,
                risk_free_rate=risk_free_rate,
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
            raise ValueError(f"Alpaca API Error: {str(e)}")