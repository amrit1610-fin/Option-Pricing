from data.market_data import MarketData
from models.heston import HestonFourierEngine

ticker = "AAPL"
expiry = "2026-08-21"
strike = 310.00
option = "Call"

data = MarketData()
fetched_data = data.get_market_data(ticker, expiry, strike, option)

print(fetched_data)

v0 = 0.04
rho = -0.7
kappa = 2
theta = 0.04
sigma_v = 0.03

engine = HestonFourierEngine(fetched_data, v0, rho, kappa, theta, sigma_v)
price = engine.calculate_price()
print("Price: ", price)

#greeks = engine.calculate_greeks()
#print("Greeks: ", greeks)