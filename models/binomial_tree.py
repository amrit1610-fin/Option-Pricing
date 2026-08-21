import numpy as np
import networkx as nx
import matplotlib.pyplot as plt


class BinomialTreeEngine:
    """
    Cox-Ross-Rubinstein (CRR) Binomial Tree Model.
    Supports both European and American options for calls and puts.
    """

    def __init__(self, market_data, N: int = 500):
        self.market_data = market_data
        self.N = N

    def _get_payoff(self, spot_prices: np.ndarray) -> np.ndarray:
        """Helper to calculate payoff arrays directly from MarketData."""
        K = self.market_data.strike_price
        if self.market_data.option_type.lower() == "call":
            return np.maximum(spot_prices - K, 0.0)
        elif self.market_data.option_type.lower() == "put":
            return np.maximum(K - spot_prices, 0.0)
        else:
            raise ValueError(f"Invalid option_type: {self.market_data.option_type}. Must be 'call' or 'put'.")

    def _build_trees(self):
        """Core logic to construct the underlying stock and option price trees."""
        S = self.market_data.spot_price
        K = self.market_data.strike_price
        T = self.market_data.time_to_expiry
        r = self.market_data.risk_free_rate
        q = self.market_data.dividend_yield
        sigma = self.market_data.volatility
        option_type = self.market_data.option_type

        # 1. Tree parameters
        dt = T / self.N
        u = np.exp(sigma * np.sqrt(dt))
        d = 1.0 / u
        p = (np.exp((r - q) * dt) - d) / (u - d)
        discount = np.exp(-r * dt)

        # 2. Initialize lattice grids
        stock_tree = np.zeros((self.N + 1, self.N + 1))
        option_tree = np.zeros((self.N + 1, self.N + 1))

        # 3. Forward pass: Build stock tree
        for i in range(self.N + 1):
            for j in range(i + 1):
                stock_tree[j, i] = S * (u ** (i - j)) * (d ** j)

        # 4. Terminal payoff at expiration
        terminal_prices = stock_tree[:, self.N]
        option_tree[:, self.N] = self._get_payoff(terminal_prices)

        # 5. Backward induction pass
        is_american = self.market_data.exercise_style.lower() == "american"

        for i in range(self.N - 1, -1, -1):
            for j in range(i + 1):
                # Expected discounted value (continuation value)
                expected_val = discount * (p * option_tree[j, i + 1] + (1.0 - p) * option_tree[j + 1, i + 1])

                if is_american:
                    # Intrinsic value upon immediate exercise
                    spot_now = stock_tree[j, i]
                    intrinsic_val = spot_now - K if option_type.lower() == "call" else K - spot_now
                    option_tree[j, i] = max(expected_val, intrinsic_val, 0.0)
                else:
                    option_tree[j, i] = expected_val

        return stock_tree, option_tree

    def calculate_price(self, **kwargs) -> float:
        """
        Pricing interface. Compatible with NumericalGreeks engine.
        """
        _, option_tree = self._build_trees()
        return float(option_tree[0, 0])


    def plot_binomial_tree(self, display_steps: int = None):
        """
        Visualizes the binomial lattice using NetworkX and Matplotlib.
        
        Args:
            display_steps: Optional step limit for plotting (trees with N > 10 become unreadable).
        """
        steps = display_steps if display_steps is not None else min(self.N, 5)
        
        # Build smaller sub-tree for visual rendering if N is large
        if steps != self.N:
            sub_engine = BinomialTreeEngine(market_data=self.market_data, N=steps)
            stock_tree, option_tree = sub_engine._build_trees()
        else:
            stock_tree, option_tree = self._build_trees()

        G = nx.DiGraph()
        pos = {}
        labels = {}

        for i in range(steps + 1):
            for j in range(i + 1):
                node_id = f"{i}_{j}"
                G.add_node(node_id)
                pos[node_id] = (i, i - 2 * j)
                labels[node_id] = f"S:{stock_tree[j, i]:.1f}\nV:{option_tree[j, i]:.2f}"

                if i < steps:
                    G.add_edge(node_id, f"{i+1}_{j}")
                    G.add_edge(node_id, f"{i+1}_{j+1}")

        plt.figure(figsize=(12, 7))
        nx.draw(
            G, pos, labels=labels, with_labels=True,
            node_size=2200, node_color="lightsteelblue",
            font_size=8, font_weight="bold", arrows=True,
            edge_color="gray"
        )

        title_str = (
            f"{steps}-Step Binomial Tree | "
            f"{self.market_data.exercise_style.capitalize()} {self.market_data.option_type.upper()} | "
            f"K = {self.market_data.strike_price}"
        )
        plt.title(title_str, fontsize=12)
        plt.margins(0.15)
        plt.show()