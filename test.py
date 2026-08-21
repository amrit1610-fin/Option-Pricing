from data.market_data import MarketData
from models.black_scholes import BlackScholesEngine

ticker = "AAPL"
expiry = "2026-08-21"
strike = 317.00
option = "Call"

data = MarketData()
fetched_data = data.get_market_data(ticker, expiry, strike, option)

print(fetched_data)

engine = BlackScholesEngine(fetched_data)
price = engine.calculate_price()
print("Price: ", price)