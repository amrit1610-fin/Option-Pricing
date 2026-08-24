import yfinance as yf
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
from data.market_data_layout import MarketDataLayout

class MarketData:
    def __init__(self, risk_free_rate: float = 0.045):
        """
        Initializes the extractor. 
        risk_free_rate is defaulted to 4.5% but can be dynamically updated.
        """
        self.risk_free_rate = risk_free_rate

    def _determine_exercise_style(self, ticker: str) -> str:
        """
        Automatically classifies the exercise style.
        Major indices are European-settled. Standard equities are American.
        """
        european_indices = ["^SPX", "^NDX", "^RUT", "^VIX"]
        return "european" if ticker.upper() in european_indices else "american"

    def _calculate_dte_years(self, expiration_date: str) -> float:
        """Calculates time to expiry in years based on today's date."""
        exp_date_obj = datetime.strptime(expiration_date, "%Y-%m-%d")
        dte_days = (exp_date_obj - datetime.now()).days
        
        # Enforce a minimum time of 0.0001 years to prevent division-by-zero in engines
        return max(dte_days / 365.25, 0.0001) 

    def get_contract_data(
        self, 
        ticker_symbol: str, 
        expiration_date: str, 
        target_strike: float, 
        option_type: str = "put"
    ) -> MarketDataLayout:
        """
        Fetches live data from Yahoo Finance and packs it into the standardized layout.
        """
        ticker = yf.Ticker(ticker_symbol)
        
        # 1. Fetch Spot Price & Dividend Yield
        hist = ticker.history(period="5d")
        if not hist.empty:
            spot_price = float(hist["Close"].iloc[-1])
        else:
            spot_price = float(ticker.fast_info.get("last_price", 0.0))

        if spot_price <= 0.0:
            raise ValueError(f"Failed to fetch valid spot price for {ticker_symbol}. Market data may be unavailable.")
        
        # Safely extract dividend yield (Yahoo sometimes omits this for indices)
        try:
            div_yield = float(ticker.info.get("dividendYield", 0.0) or 0.0)
        except Exception:
            div_yield = 0.0

        # 2. Fetch Options Chain
        try:
            chain = ticker.option_chain(expiration_date)
        except Exception as e:
            raise ValueError(f"Could not fetch options chain for {ticker_symbol} on {expiration_date}. Error: {e}")

        df = chain.puts if option_type.lower() == "put" else chain.calls

        # 3. Find the specific strike
        contract_row = df[df["strike"] == target_strike]
        if contract_row.empty:
            raise ValueError(f"Strike {target_strike} not found for {ticker_symbol} on {expiration_date}.")

        # 4. Extract Pricing & Volatility
        bid = float(contract_row["bid"].iloc[0])
        ask = float(contract_row["ask"].iloc[0])
        last_price = float(contract_row["lastPrice"].iloc[0])
        
        # Yahoo provides its own implied volatility calculation
        iv = float(contract_row["impliedVolatility"].iloc[0])

        # Calculate mid-price. If the spread is 0 (illiquid), fallback to the last traded price.
        market_price = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else last_price

        # 5. Build and return the standardized layout
        return MarketDataLayout(
            spot_price=spot_price,
            strike_price=target_strike,
            risk_free_rate=self.risk_free_rate,
            time_to_expiry=self._calculate_dte_years(expiration_date),
            option_type=option_type.lower(),
            exercise_style=self._determine_exercise_style(ticker_symbol),
            dividend_yield=div_yield,
            volatility=iv,
            market_price=market_price
        )

