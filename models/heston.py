import numpy as np

class HestonFourierEngine:
    """
    Fourier transform pricing for the Heston Model using the Carr-Madan (1999) FFT method.
    Fast and accurate, but restricted to European options.
    """

    def __init__(self, market_data, v0: float, rho: float, kappa: float, theta: float, sigma_v: float):
        self.market_data = market_data
        self.v0 = v0
        self.rho = rho
        self.kappa = kappa
        self.theta = theta
        self.sigma_v = sigma_v
        
        self.x0 = np.log(self.market_data.spot_price)
        self.i = 1j

    def _cf(self, u):
        """Heston Characteristic Function (Albrecher formulation)"""
        r = self.market_data.risk_free_rate
        q = self.market_data.dividend_yield
        T = self.market_data.time_to_expiry
        
        a = self.kappa * self.theta
        b = self.kappa - (self.rho * self.sigma_v * self.i * u)
        d = np.sqrt(b**2 + self.sigma_v**2 * (self.i * u + u**2))
        g = (b - d) / (b + d)

        eDT = np.exp(-d * T)
        one_minus_g_eDT = 1 - g * eDT
        one_minus_g     = 1 - g
        
        one_minus_g_eDT = np.where(np.abs(one_minus_g_eDT) < 1e-15, 1e-15, one_minus_g_eDT)
        one_minus_g     = np.where(np.abs(one_minus_g)     < 1e-15, 1e-15, one_minus_g)

        C = self.i * u * (r - q) * T + (a / (self.sigma_v**2)) * ((b - d) * T - 2.0 * np.log(one_minus_g_eDT / one_minus_g))
        D = ((b - d) / (self.sigma_v**2)) * ((1 - eDT) / one_minus_g_eDT)
        
        return np.exp(C + D * self.v0 + self.i * u * self.x0)

    def _fft_calls(self, N: int = 4096, eta: float = 0.25, alpha: float = 1.5):
        """Computes call prices over a grid of strikes using FFT."""
        r = self.market_data.risk_free_rate
        T = self.market_data.time_to_expiry
        
        n = np.arange(N)
        v = eta * n
        u = v - (alpha + 1) * self.i
        ert = np.exp(-r * T)
        
        psi = (ert * self._cf(u)) / (alpha**2 + alpha - v**2 + self.i * (2 * alpha + 1) * v)
        
        w = np.ones(N)
        w[1:N-1:2] = 4
        w[2:N-2:2] = 2
        w = w * (eta / 3.0)

        lam = 2.0 * np.pi / (N * eta)   
        b   = 0.5 * N * lam             
        x   = psi * np.exp(self.i * b * v) * w

        F = np.fft.fft(x)
        F = np.real(F) 

        j = np.arange(N)
        k = -b + j * lam                
        K = np.exp(k)

        calls = np.exp(-alpha * k) / np.pi * F
        order = np.argsort(K)
        return K[order], np.maximum(calls[order], 0.0)

    def calculate_price(self, **kwargs) -> float:
        """
        Extracts the precise price for the specified strike using linear interpolation on the FFT grid.
        Includes put-call parity conversion if the option is a put.
        """
        target_K = self.market_data.strike_price
        K_grid, C_grid = self._fft_calls()
        
        # Linear interpolation for the Call price
        if target_K <= K_grid[0]:
            call_price = C_grid[0]
        elif target_K >= K_grid[-1]:
            call_price = C_grid[-1]
        else:
            idx = np.searchsorted(K_grid, target_K)
            x0, x1 = K_grid[idx-1], K_grid[idx]
            y0, y1 = C_grid[idx-1], C_grid[idx]
            call_price = y0 + (y1 - y0) * (target_K - x0) / (x1 - x0)

        # Return call directly, or convert to put via Put-Call Parity
        if self.market_data.option_type.lower() == 'call':
            return float(call_price)
        elif self.market_data.option_type.lower() == 'put':
            S = self.market_data.spot_price
            K = self.market_data.strike_price
            T = self.market_data.time_to_expiry
            r = self.market_data.risk_free_rate
            q = self.market_data.dividend_yield
            
            put_price = call_price - S * np.exp(-q * T) + K * np.exp(-r * T)
            return float(max(put_price, 0.0))
        else:
            raise ValueError("Option type must be 'call' or 'put'.")


class HestonMonteCarloEngine:
    """
    Monte Carlo simulation of the Heston Model using the Full Truncation scheme.
    """
    def __init__(self, market_data, v0: float, rho: float, kappa: float, theta: float, sigma_v: float, steps: int = 100, paths: int = 10000):
        self.market_data = market_data
        self.v0 = v0
        self.rho = rho
        self.kappa = kappa
        self.theta = theta
        self.sigma_v = sigma_v
        self.steps = steps
        self.paths = paths

    def _generate_paths(self, seed: int = None) -> np.ndarray:
        if seed is not None:
            np.random.seed(seed)
            
        S0 = self.market_data.spot_price
        r = self.market_data.risk_free_rate
        q = self.market_data.dividend_yield
        T = self.market_data.time_to_expiry
        
        dt = T / self.steps       

        Z1 = np.random.standard_normal(size=(self.paths, self.steps))
        Z2 = np.random.standard_normal(size=(self.paths, self.steps))

        W1 = Z1
        W2 = self.rho * Z1 + np.sqrt(1 - self.rho**2) * Z2

        S = np.zeros((self.paths, self.steps + 1))
        v = np.zeros((self.paths, self.steps + 1))

        S[:, 0] = S0
        v[:, 0] = self.v0

        for t in range(self.steps):
            v_pos = np.maximum(v[:, t], 0)
            S[:, t+1] = S[:, t] * np.exp((r - q - 0.5 * v_pos) * dt + np.sqrt(v_pos * dt) * W1[:, t])
            v[:, t+1] = v[:, t] + (self.kappa * (self.theta - v_pos) * dt) + (self.sigma_v * np.sqrt(v_pos * dt) * W2[:, t])

        return S

    def calculate_price(self, **kwargs) -> float:
        """
        Executes the pricing. Compatible with the NumericalGreeks engine (listens for 'seed').
        """
        seed = kwargs.get('seed', None)
        paths = self._generate_paths(seed)
        
        # Calculate terminal payoffs directly from MarketData
        terminal_prices = paths[:, -1]
        K = self.market_data.strike_price
        
        if self.market_data.option_type.lower() == 'call':
            simulated_payoffs = np.maximum(terminal_prices - K, 0.0)
        elif self.market_data.option_type.lower() == 'put':
            simulated_payoffs = np.maximum(K - terminal_prices, 0.0)
        else:
            raise ValueError("Option type must be 'call' or 'put'.")
        
        r = self.market_data.risk_free_rate
        T = self.market_data.time_to_expiry
        discount_factor = np.exp(-r * T)
        
        discounted_payoffs = discount_factor * simulated_payoffs
        return float(np.mean(discounted_payoffs))