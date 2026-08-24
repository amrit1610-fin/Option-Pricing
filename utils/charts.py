import numpy as np
from scipy.stats import norm
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class ChartGenerator:
    """
    Generates full quantitative visualizations using Plotly.
    Includes comprehensive Greeks, multi-colored MC paths, and model convergence.
    """
    def __init__(self, market_data):
        self.S = market_data.spot_price
        self.K = market_data.strike_price
        self.T = max(market_data.time_to_expiry, 0.0001)
        self.r = market_data.risk_free_rate
        self.sigma = max(market_data.volatility or 0.20, 0.001)
        self.opt_type = market_data.option_type.lower()

    def show_dashboard(self):
        """Builds a 5-panel interactive dashboard and pops it open."""
        # 3 Rows: Top two rows are split (2x2), bottom row spans both columns
        fig = make_subplots(
            rows=3, cols=2, 
            specs=[[{}, {}], [{}, {}], [{"colspan": 2}, None]],
            subplot_titles=(
                "1. Payoff Profile", 
                "2. Probability Density", 
                "3. Full Greeks Sensitivity", 
                "4. Monte Carlo Paths",
                "5. Model Convergence (Binomial vs MC)"
            ),
            vertical_spacing=0.1
        )

        # -------------------------------------------------------------
        # 1. Payoff Math
        # -------------------------------------------------------------
        spot_range = np.linspace(max(0.01, self.S * 0.5), self.S * 1.5, 100)
        payoff = np.maximum(spot_range - self.K, 0) if self.opt_type == "call" else np.maximum(self.K - spot_range, 0)
        
        d1 = (np.log(spot_range / self.K) + (self.r + 0.5 * self.sigma**2) * self.T) / (self.sigma * np.sqrt(self.T))
        d2 = d1 - self.sigma * np.sqrt(self.T)
        
        if self.opt_type == "call":
            price_curve = spot_range * norm.cdf(d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(d2)
        else:
            price_curve = self.K * np.exp(-self.r * self.T) * norm.cdf(-d2) - spot_range * norm.cdf(-d1)

        # -------------------------------------------------------------
        # 2. PDF Math
        # -------------------------------------------------------------
        mu = np.log(self.S) + (self.r - 0.5 * self.sigma**2) * self.T
        std_dev = self.sigma * np.sqrt(self.T)
        pdf = (1.0 / (spot_range * std_dev * np.sqrt(2 * np.pi))) * np.exp(-((np.log(spot_range) - mu)**2) / (2 * std_dev**2))

        # -------------------------------------------------------------
        # 3. Greeks Math (Scaled for single-axis visibility)
        # -------------------------------------------------------------
        gamma = (norm.pdf(d1) / (spot_range * self.sigma * np.sqrt(self.T))) * 100  # Scaled by 100
        vega = (spot_range * norm.pdf(d1) * np.sqrt(self.T)) / 100  # 1% IV change
        
        if self.opt_type == "call":
            delta = norm.cdf(d1)
            theta = (-(spot_range * norm.pdf(d1) * self.sigma) / (2 * np.sqrt(self.T)) - self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(d2)) / 365
            rho = (self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(d2)) / 100
        else:
            delta = norm.cdf(d1) - 1.0
            theta = (-(spot_range * norm.pdf(d1) * self.sigma) / (2 * np.sqrt(self.T)) + self.r * self.K * np.exp(-self.r * self.T) * norm.cdf(-d2)) / 365
            rho = (-self.K * self.T * np.exp(-self.r * self.T) * norm.cdf(-d2)) / 100

        # -------------------------------------------------------------
        # 4. Monte Carlo Math
        # -------------------------------------------------------------
        np.random.seed(42)
        num_paths, num_steps = 30, 50
        dt_mc = self.T / num_steps
        drift = (self.r - 0.5 * self.sigma**2) * dt_mc
        vol_step = self.sigma * np.sqrt(dt_mc)
        increments = np.random.normal(0, 1, size=(num_paths, num_steps))
        paths = np.zeros((num_paths, num_steps + 1))
        paths[:, 0] = self.S
        paths[:, 1:] = self.S * np.exp(np.cumsum(drift + vol_step * increments, axis=1))
        time_grid = np.linspace(0, self.T, num_steps + 1)

        # -------------------------------------------------------------
        # 5. Convergence Math
        # -------------------------------------------------------------
        # Define simulation intensity levels
        levels = ["L1", "L2", "L3", "L4", "L5"]
        bt_steps_list = [10, 25, 50, 100, 200]
        mc_paths_list = [100, 500, 1000, 5000, 10000]
        bt_prices, mc_prices = [], []

        # Analytical Target Price (at Spot)
        d1_s = (np.log(self.S / self.K) + (self.r + 0.5 * self.sigma**2) * self.T) / (self.sigma * np.sqrt(self.T))
        d2_s = d1_s - self.sigma * np.sqrt(self.T)
        bsm_target = (self.S * norm.cdf(d1_s) - self.K * np.exp(-self.r * self.T) * norm.cdf(d2_s)) if self.opt_type == "call" else (self.K * np.exp(-self.r * self.T) * norm.cdf(-d2_s) - self.S * norm.cdf(-d1_s))

        for steps, paths_count in zip(bt_steps_list, mc_paths_list):
            # Binomial Calculation
            dt = self.T / steps
            u = np.exp(self.sigma * np.sqrt(dt))
            d = 1.0 / u
            p = (np.exp(self.r * dt) - d) / (u - d)
            st_nodes = self.S * (u ** np.arange(steps, -1, -1)) * (d ** np.arange(0, steps + 1, 1))
            c_nodes = np.maximum(st_nodes - self.K, 0) if self.opt_type == "call" else np.maximum(self.K - st_nodes, 0)
            for _ in range(steps - 1, -1, -1):
                c_nodes = np.exp(-self.r * dt) * (p * c_nodes[:-1] + (1.0 - p) * c_nodes[1:])
            bt_prices.append(c_nodes[0])
            
            # Fast Monte Carlo Calculation
            dt_mc_conv = self.T / 50
            drift_mc = (self.r - 0.5 * self.sigma**2) * dt_mc_conv
            vol_step_mc = self.sigma * np.sqrt(dt_mc_conv)
            increments_mc = np.random.normal(0, 1, size=(paths_count, 50))
            sim_paths = self.S * np.exp(np.cumsum(drift_mc + vol_step_mc * increments_mc, axis=1))
            terminal_prices = sim_paths[:, -1]
            payoffs_mc = np.maximum(terminal_prices - self.K, 0) if self.opt_type == "call" else np.maximum(self.K - terminal_prices, 0)
            mc_prices.append(np.mean(payoffs_mc) * np.exp(-self.r * self.T))


        # =============================================================
        # TRACE INJECTION
        # =============================================================
        
        # 1. Payoff
        fig.add_trace(go.Scatter(x=spot_range, y=payoff, name="Payoff", line=dict(color="#22c55e")), row=1, col=1)
        fig.add_trace(go.Scatter(x=spot_range, y=price_curve, name="Value", line=dict(color="#eab308", dash="dot")), row=1, col=1)
        
        # 2. PDF
        fig.add_trace(go.Scatter(x=spot_range, y=pdf, name="PDF", fill="tozeroy", line=dict(color="#0ea5e9")), row=1, col=2)
        fig.add_trace(go.Scatter(x=[self.K, self.K], y=[0, np.max(pdf)], name="Strike", line=dict(color="#ef4444", dash="dash")), row=1, col=2)
        
        # 3. All Greeks
        fig.add_trace(go.Scatter(x=spot_range, y=delta, name="Delta", line=dict(color="#ec4899")), row=2, col=1)
        fig.add_trace(go.Scatter(x=spot_range, y=gamma, name="Gamma (x100)", line=dict(color="#a855f7", dash="dot")), row=2, col=1)
        fig.add_trace(go.Scatter(x=spot_range, y=vega, name="Vega", line=dict(color="#f97316")), row=2, col=1)
        fig.add_trace(go.Scatter(x=spot_range, y=theta, name="Theta", line=dict(color="#14b8a6")), row=2, col=1)
        fig.add_trace(go.Scatter(x=spot_range, y=rho, name="Rho", line=dict(color="#ef4444")), row=2, col=1)
        
        # 4. Multi-colored Monte Carlo
        for i in range(num_paths):
            path_color = f'hsl({int(360 * i / num_paths)}, 80%, 65%)'
            fig.add_trace(go.Scatter(x=time_grid, y=paths[i], showlegend=False, line=dict(color=path_color, width=1.5), opacity=0.4), row=2, col=2)
        fig.add_trace(go.Scatter(x=[0, self.T], y=[self.K, self.K], name="Strike", line=dict(color="#ef4444", dash="dash", width=3)), row=2, col=2)

        # 5. Convergence Tracking
        fig.add_trace(go.Scatter(x=levels, y=bt_prices, mode="lines+markers", name="Binomial Lattice", line=dict(color="#38bdf8", width=3), marker=dict(size=8)), row=3, col=1)
        fig.add_trace(go.Scatter(x=levels, y=mc_prices, mode="lines+markers", name="Monte Carlo", line=dict(color="#f43f5e", width=3), marker=dict(size=8)), row=3, col=1)
        fig.add_trace(go.Scatter(x=levels, y=[bsm_target]*len(levels), name="Analytical (BSM)", line=dict(color="#22c55e", dash="dash", width=2)), row=3, col=1)

        # =============================================================
        # LAYOUT & RENDERING
        # =============================================================
        fig.update_layout(
            title_text=f"Quantitative Risk Dashboard | {self.opt_type.upper()} | Spot: ${self.S:.2f} | Strike: ${self.K:.2f} | DTE: {self.T:.3f} Yrs",
            template="plotly_dark", 
            height=1100,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Ensure the convergence chart X-axis reflects computational scale
        fig.update_xaxes(title_text="Intensity (BT Steps / MC Paths)", tickvals=levels, ticktext=[f"{bt} / {mc}" for bt, mc in zip(bt_steps_list, mc_paths_list)], row=3, col=1)
        
        fig.show()