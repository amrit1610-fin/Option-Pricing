import os
import requests
from datetime import datetime

from data.market_data_layout import MarketDataLayout

class MarketData:
    def __init__(self):
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.headers = {
            "APCA-API-KEY-ID": self.api_key or "",
            "APCA-API-SECRET-KEY": self.secret_key or "",
            "Accept": "application/json"
        }
        self.base_url = "https://data.alpaca.markets"

    def _generate_occ_symbol(self, ticker: str, expiration_date: str, strike_price: float, option_type: str) -> str:
        clean_ticker = ticker.upper().replace("^", "")
        ticker_padded = clean_ticker.ljust(6)
        exp_date_obj = datetime.strptime(expiration_date, "%Y-%m-%d")
        date_str = exp_date_obj.strftime("%y%m%d")
        call_put = 'C' if option_type.lower() == 'call' else 'P'
        strike_str = f"{int(strike_price * 1000):08d}"
        return f"{ticker_padded}{date_str}{call_put}{strike_str}"

    def get_market_data(self, ticker: str, expiration_date: str, strike_price: float, option_type: str) -> MarketDataModel:
        if not self.api_key or not self.secret_key:
            raise ValueError("SYSTEM ERROR: Alpaca API Keys are missing on Render environment variables.")

        clean_ticker = ticker.upper().replace("^", "")
        equity_proxy = "SPY" if clean_ticker == "SPX" else "QQQ" if clean_ticker == "NDX" else clean_ticker

        try:
            # 1. Spot Price
            spot_url = f"{self.base_url}/v2/stocks/{equity_proxy}/trades/latest"
            spot_res = requests.get(spot_url, headers=self.headers)
            
            if spot_res.status_code == 401:
                raise ValueError("Alpaca API Keys are invalid.")
            elif spot_res.status_code == 429:
                raise ValueError("Alpaca API Rate Limit Hit.")
            
            spot_data = spot_res.json()
            if "trade" not in spot_data:
                raise ValueError(f"Could not fetch spot price for {equity_proxy}.")
            
            spot_price = float(spot_data["trade"]["p"])
            if clean_ticker == "SPX": 
                spot_price *= 10 

            risk_free_rate = 0.05

            # 2. Options Data
            occ_symbol = self._generate_occ_symbol(clean_ticker, expiration_date, strike_price, option_type)
            opt_url = f"{self.base_url}/v1beta1/options/quotes/latest?symbols={occ_symbol}"
            opt_res = requests.get(opt_url, headers=self.headers)
            
            market_price = 0.0
            volatility = 0.20 
            
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

            # 3. Time to Expiry
            exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
            days_to_expiry = (exp_date - datetime.now()).days
            time_to_expiry = max(days_to_expiry / 365.0, 0.001)

            # 4. Exercise Style
            european_indices = ["SPX", "SPXW", "XSP", "NDX", "RUT", "VIX", "DJX", "XEO", "MNX"]
            exercise_style = "european" if clean_ticker in european_indices else "american"

            # Pass values in the exact positional/keyword format matching MarketDataModel
            return MarketDataLayout(
                ticker=clean_ticker,
                spot_price=spot_price,
                strike_price=strike_price,
                risk_free_rate=risk_free_rate,
                time_to_expiry=time_to_expiry,
                volatility=volatility,
                market_price=market_price,
                exercise_style=exercise_style,
                option_type=option_type
            )
            
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise ValueError(f"Market Data Error: {str(e)}")