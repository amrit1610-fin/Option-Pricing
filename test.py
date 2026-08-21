from data.market_data import MarketData
from models.monte_carlo import MonteCarloEngine

ticker = "AAPL"
expiry = "2026-08-21"
strike = 310.00
option = "Call"

data = MarketData()
fetched_data = data.get_market_data(ticker, expiry, strike, option)

print(fetched_data)

engine = MonteCarloEngine(fetched_data)
price = engine.calculate_price()
print("Price: ", price)

#greeks = engine.calculate_greeks()
#print("Greeks: ", greeks)