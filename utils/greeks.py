from typing import Dict, Any

class NumericalGreeks:
    """
    Calculates Delta, Gamma, Theta, Vega, and Rho using finite difference methods.
    """
    
    @staticmethod
    def calculate_greeks(engine: Any, is_monte_carlo: bool = False) -> Dict[str, float]:
        # Lock the seed for Monte Carlo to eliminate variance noise between bumps
        kwargs = {"seed": 42} if is_monte_carlo else {}
        
        # 1. Get Base Price
        base_price = engine.calculate_price(**kwargs)
        
        # 2. Access the single source of truth for market data
        md = engine.market_data
        
        # 3. Define bump sizes
        dS = max(md.spot_price * 0.001, 0.01)  # 0.1% or minimum 1 cent
        dR = 0.0001                            # 1 basis point
        dVol = 0.01                            # 1% implied volatility
        
        # SAFEGUARD: Ensure time bump (dT) never pushes time_to_expiry below zero
        dT = 1.0 / 365.0                       # Default 1 day
        if md.time_to_expiry <= dT:
            # If less than 1 day to expiry, bump time by half the remaining time
            dT = md.time_to_expiry * 0.5 
        
        # Helper function to bump, price, and revert safely
        def get_bumped_price(attr: str, bump_amt: float) -> float:
            original_val = getattr(md, attr)
            setattr(md, attr, original_val + bump_amt)
            price = engine.calculate_price(**kwargs)
            setattr(md, attr, original_val)  # Revert back instantly
            return price

        # 4. Calculate Greeks
        
        # Delta & Gamma (Spot Price Bumps)
        price_up_s = get_bumped_price('spot_price', dS)
        price_dn_s = get_bumped_price('spot_price', -dS)
        delta = (price_up_s - price_dn_s) / (2 * dS)
        gamma = (price_up_s - 2 * base_price + price_dn_s) / (dS ** 2)
        
        # Theta (Time Bump)
        # Theta is usually represented as the loss in value per day passing.
        price_time_pass = get_bumped_price('time_to_expiry', -dT)
        
        # Calculate annualized theta, then convert to daily decay
        theta_annual = (price_time_pass - base_price) / dT
        theta_daily = theta_annual / 365.0
        
        # Rho (Interest Rate Bump)
        price_up_r = get_bumped_price('risk_free_rate', dR)
        price_dn_r = get_bumped_price('risk_free_rate', -dR)
        rho_annual = (price_up_r - price_dn_r) / (2 * dR)
        rho = rho_annual / 100.0  # Scaled to represent a 1% rate change
        
        # Vega (Volatility Bump)
        # We only calculate Vega if the engine relies on Implied Volatility.
        # Heston models use stochastic variance parameters (v0, sigma_v), not a flat IV.
        vega = 0.0
        if hasattr(md, 'volatility') and md.volatility is not None:
            price_up_v = get_bumped_price('volatility', dVol)
            price_dn_v = get_bumped_price('volatility', -dVol)
            vega_annual = (price_up_v - price_dn_v) / (2 * dVol)
            vega = vega_annual / 100.0  # Scaled to represent a 1% IV change
            
        return {
            "price": base_price,
            "delta": delta,
            "gamma": gamma,
            "vega": vega,
            "theta": theta_daily,
            "rho": rho
        }