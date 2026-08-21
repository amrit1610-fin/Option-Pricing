import copy
from typing import Dict, Any

class NumericalGreeks:
    @staticmethod
    def calculate_greeks(engine: Any, is_monte_carlo: bool = False) -> Dict[str, float]:
        kwargs = {"seed": 42} if is_monte_carlo else {}
        
        base_price = engine.calculate_price(**kwargs)
        md = engine.md # Assuming all engines bind MarketData to self.md
        
        # Refined bump sizes
        dS = max(md.spot_price * 0.001, 0.01) # 0.1% or minimum 1 cent
        dT = 1.0 / 365.0
        dR = 0.0001
        dVol = 0.01
        
        def get_bumped_price(attr: str, bump_amt: float):
            original_val = getattr(md, attr)
            setattr(md, attr, original_val + bump_amt)
            price = engine.calculate_price(**kwargs)
            setattr(md, attr, original_val) 
            return price

        # Delta & Gamma
        price_up_s = get_bumped_price('spot_price', dS)
        price_dn_s = get_bumped_price('spot_price', -dS)
        delta = (price_up_s - price_dn_s) / (2 * dS)
        gamma = (price_up_s - 2 * base_price + price_dn_s) / (dS ** 2)
        
        # Theta, Rho, Vega
        price_time_pass = get_bumped_price('time_to_expiry', -dT)
        theta = (price_time_pass - base_price) / dT
        
        price_up_r = get_bumped_price('risk_free_rate', dR)
        price_dn_r = get_bumped_price('risk_free_rate', -dR)
        rho = (price_up_r - price_dn_r) / (2 * dR)
        
        price_up_v = get_bumped_price('volatility', dVol)
        price_dn_v = get_bumped_price('volatility', -dVol)
        vega = (price_up_v - price_dn_v) / (2 * dVol)
            
        return {
            "price": base_price,
            "delta": delta,
            "gamma": gamma,
            "vega": vega / 100.0, 
            "theta": theta / 365.0, 
            "rho": rho / 100.0
        }