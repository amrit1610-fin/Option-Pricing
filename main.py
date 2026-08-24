import sys
from data.market_data import MarketData 
from models.black_scholes import BlackScholesEngine
from models.binomial_tree import BinomialTreeEngine
from models.monte_carlo import MonteCarloEngine
from utils.charts import ChartGenerator
from utils.greeks import NumericalGreeks
from utils.implied_vol import ImpliedVolatility

def run_terminal():
    print("=" * 70)
    print(" INSTITUTIONAL OPTIONS PRICING TERMINAL ".center(70))
    print("=" * 70)

    extractor = MarketData(risk_free_rate=0.045)

    ticker = input("Enter Ticker (e.g., ^SPX, AAPL) [example: AAPL]: ").strip().upper() 
    expiry = input("Enter Expiration (YYYY-MM-DD) [example: 2026-09-18]: ").strip() 
    strike_in = input("Enter Target Strike [example: 225.0]: ").strip()
    target_strike = float(strike_in)
    opt_type = input("Option Type (call/put) [default: call]: ").strip().lower()

    try:
        print(f"\n[*] Fetching live market data for {ticker} via yfinance...")
        market_data = extractor.get_contract_data(
            ticker_symbol=ticker,
            expiration_date=expiry,
            target_strike=target_strike,
            option_type=opt_type
        )

        # =================================================================
        # IMPLIED VOLATILITY CALIBRATION
        # =================================================================
        print("[*] Calibrating True Implied Volatility from Market Premium...")
        if market_data.market_price and market_data.market_price > 0:
            # 1. Instantiate a fast analytical engine for the root-finder
            bs_solver_engine = BlackScholesEngine(market_data=market_data)
            
            # 2. Pass the engine and market premium to your static method
            true_iv = ImpliedVolatility.calculate_iv(
                engine=bs_solver_engine, 
                market_price=market_data.market_price, 
                is_monte_carlo=False
            )
            
            # 3. Overwrite the yfinance IV with your calibrated IV
            market_data.volatility = true_iv 
        else:
            print("[!] Market premium is zero (illiquid). Falling back to basic yfinance IV.")
        

        print("\n" + "-" * 70)
        print(" CONTRACT SPECIFICATIONS ".center(70))
        print("-" * 70)
        print(f" Underlying Spot: ${market_data.spot_price:.2f}")
        print(f" Target Strike:   ${market_data.strike_price:.2f}")
        print(f" Time to Expiry:  {market_data.time_to_expiry:.4f} Years")
        print(f" Market IV:       {market_data.volatility * 100:.2f}%")
        print(f" Exercise Style:  {market_data.exercise_style.upper()}")
        print("-" * 70)

        print("\n[*] Initializing Pricing Engines...")
        
        # 1. Black-Scholes Model Execution (Analytical)
        bs_engine = BlackScholesEngine(market_data=market_data)
        bs_price = bs_engine.calculate_price()
        bs_greeks = bs_engine.calculate_greeks()
        bs_results = {"price": bs_price, **bs_greeks}
        
        # 2. Binomial Tree Model Execution (Numerical Greeks)
        bt_engine = BinomialTreeEngine(market_data=market_data, N=500)
        bt_price = bt_engine.calculate_price()
        bt_results = NumericalGreeks.calculate_greeks(engine=bt_engine, is_monte_carlo=False)
        
        # 3. Monte Carlo Model Execution (Numerical Greeks)
        mc_engine = MonteCarloEngine(market_data=market_data)
        mc_price = mc_engine.calculate_price()
        mc_results = NumericalGreeks.calculate_greeks(engine=mc_engine, is_monte_carlo=True)

        # Print Risk Matrix
        print("\n" + "=" * 70)
        print(" VALUATION & SENSITIVITY MATRIX ".center(70))
        print("=" * 70)
        print(f"{'METRIC':<15} | {'BSM':<15} | {'BINOMIAL':<15} | {'MONTE CARLO':<15}")
        print("-" * 70)
        
        metrics = ["price", "delta", "gamma", "theta", "vega", "rho"]
        for m in metrics:
            bs_val = bs_results.get(m, 0.0)
            bt_val = bt_results.get(m, 0.0)
            mc_val = mc_results.get(m, 0.0)
            print(f"{m.upper():<15} | {bs_val:<15.4f} | {bt_val:<15.4f} | {mc_val:<15.4f}")
        
        print("\n[*] Generating Data Visualization Dashboard...")
        chart_gen = ChartGenerator(market_data=market_data)
        
        print("[SUCCESS] Rendering interactive dashboard in browser...")
        chart_gen.show_dashboard()
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n[!] TERMINAL FATAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_terminal()