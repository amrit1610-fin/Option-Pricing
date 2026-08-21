import yfinance as yf
from datetime import datetime, timezone
from data.market_data_layout import MarketDataLayout

class MarketData:
    """
    Fetches raw market data and formats it directly into the MarketData struct.
    """
    KNOWN_EUROPEAN_INDICES = {"^SPX", "^NDX", "^RUT", "^DJI", "^VIX"}

    def __init__(self, fallback_rate: float = 0.045):
        self.fallback_rate = fallback_rate

    def get_market_data(
        self, ticker: str, expiration_date: str, strike_price: float, option_type: str
    ) -> MarketDataLayout:
        """
        Main entry point: Fetches all required data and returns the lean pricing payload.
        """
        t = yf.Ticker(ticker)
        
        # 1. Get Spot Price
        spot_price = t.fast_info.last_price
        
        # 2. Get Exercise Style
        is_european = ticker.upper() in self.KNOWN_EUROPEAN_INDICES
        exercise_style = "european" if is_european else "american"
        
        # 3. Get Risk-Free Rate (^TNX is 10-yr treasury yield)
        r_rate = self.fallback_rate
        try:
            tnx = yf.Ticker("^TNX")
            hist = tnx.history(period="1d")
            if not hist.empty:
                r_rate = float(hist["Close"].iloc[-1]) / 100.0
        except Exception:
            pass

        # 4. Get Dividend Yield
        div_yield = float(t.info.get("dividendYield") or 0.0)

        # 5. Calculate Time to Expiry (Years)
        now = datetime.now(timezone.utc)
        expiry_dt = datetime.strptime(expiration_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        time_to_expiry = max((expiry_dt - now).total_seconds() / (365.25 * 86400), 1e-5)

        # 6. Get Implied Volatility from Option Chain
        implied_vol = 0.20 # fallback
        try:
            chain = t.option_chain(expiration_date)
            df = chain.calls if option_type.lower() == "call" else chain.puts
            # Find the closest strike to get the market implied volatility
            closest_row = df.iloc[(df['strike'] - strike_price).abs().argsort()[:1]]
            if not closest_row.empty:
                implied_vol = float(closest_row['impliedVolatility'].iloc[0])
        except Exception:
            pass

        return MarketDataLayout(
            spot_price=float(spot_price),
            strike_price=strike_price,
            risk_free_rate=r_rate,
            time_to_expiry=time_to_expiry,
            option_type=option_type.lower(),
            exercise_style=exercise_style,
            dividend_yield=div_yield,
            volatility=implied_vol
        )