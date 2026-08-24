# 📈 Quantitative Options Pricing & Risk Terminal

An institutional-grade derivatives pricing, volatility calibration, and risk management terminal written in Python. The engine ingests live market options chains via `yfinance`, calibrates true implied volatility using root-finding algorithms, executes multiple valuation models (Analytical, Lattice, and Stochastic Simulation), calculates numerical and analytical Greeks via finite difference bump-and-revalue methods, and renders an interactive multi-panel Plotly risk dashboard.

---

## 🏛️ System Architecture


```

```
                              +-----------------------+
                              |   Yahoo Finance API   |
                              +-----------+-----------+
                                          |
                                          v
                              +-----------------------+
                              | LiveMarketDataExtractor|
                              +-----------+-----------+
                                          |
                                          v
                              +-----------------------+
                              |   MarketDataLayout    | <---+ (Decoupled In-Memory Container)
                              +-----------+-----------+
                                          |
                  +-----------------------+-----------------------+
                  |                                               |
                  v                                               v
    +---------------------------+                   +---------------------------+
    | Implied Volatility Solver |                   |    Pricing Engines Core   |
    |   (Brent's Root-Finding)  |                   +-------------+-------------+
    +-------------+-------------+                                 |
                  | (Calibrated IV)                               |
                  +-----------------------------------------------+
                                          |
                  +-----------------------+-----------------------+
                  |                       |                       |
                  v                       v                       v
        +-------------------+   +-------------------+   +-------------------+
        |   Black-Scholes   |   |   Binomial Tree   |   |    Monte Carlo    |
        |     Engine        |   |    (CRR Lattice)  |   |     (GBM Paths)   |
        +---------+---------+   +---------+---------+   +---------+---------+
                  |                       |                       |
                  | (Analytical)          | (Finite Difference)   | (Finite Difference)
                  v                       v                       v
        +-------------------------------------------------------------------+
        |               Numerical Greeks & Sensitivity Matrix               |
        |                (Delta, Gamma, Vega, Theta, Rho)                   |
        +---------------------------------+---------------------------------+
                                          |
                                          v
        +-------------------------------------------------------------------+
        |                5-Panel Interactive Plotly Dashboard               |
        |     [Payoff | PDF | Full Greeks | MC Paths | Model Convergence]   |
        +-------------------------------------------------------------------+

```

```

---

## 🚀 Key Features & Quantitative Methodology

### 1. Robust Live Market Ingestion & Standardization
* Ingests real-time underlying spot prices, option chains, bid/ask spreads, and days-to-expiration (DTE).
* Automatically classifies exercise style (`American` for single equities, `European` for cash-settled major indices like `^SPX`, `^NDX`, `^RUT`, `^VIX`).
* Packs all attributes into a decoupled, strongly typed `MarketDataLayout` object for zero-side-effect parameter mutations during Greek evaluations.

### 2. Numerical Implied Volatility Calibration
* Replaces proprietary, black-box vendor IV estimates by calibrating directly against live option mid-market premiums:
  $$\text{Mid Price} = \frac{\text{Bid} + \text{Ask}}{2}$$
* Solves the inverse pricing problem using **Brent’s Method (`scipy.optimize.brentq`)**, finding the root $\sigma_{\text{implied}}$ such that:
  $$f(\sigma) = V_{\text{model}}(S, K, T, r, q, \sigma) - P_{\text{market}} = 0$$

### 3. Multi-Model Valuation Core
* **Black-Scholes-Merton (BSM) Analytical Engine:** Closed-form benchmark pricing for European options with continuous dividend yields ($q$).
* **Cox-Ross-Rubinstein (CRR) Binomial Lattice Engine:** Discrete multi-step lattice ($N=500$) supporting backward induction and early exercise boundaries for American options.
* **Monte Carlo Simulation Engine:** Simulates vectorized Geometric Brownian Motion (GBM) paths with terminal payoff discounting:
  $$S(t + \Delta t) = S(t) \exp\left(\left(r - q - \frac{1}{2}\sigma^2\right)\Delta t + \sigma \sqrt{\Delta t} \, Z\right), \quad Z \sim \mathcal{N}(0, 1)$$

### 4. Dual-Mode Greek Risk Attribution
* **Analytical Greeks:** Exact partial differential equations computed closed-form for BSM.
* **Finite-Difference Numerical Greeks:** Universal bump-and-revalue engine calculating first and second-order sensitivities across discrete and stochastic models:
  * **Delta ($\Delta$):** Central difference bump $\pm 0.1\%$ spot price.
  * **Gamma ($\Gamma$):** Second-order central difference curvature.
  * **Vega ($\mathcal{V}$):** $\pm 1.0\%$ implied volatility bump.
  * **Theta ($\Theta$):** Forward time-decay translation (scaled to 1 calendar day).
  * **Rho ($\rho$):** $\pm 1 \text{ bps}$ interest rate shock (scaled to $1.0\%$).
* **Monte Carlo Seed Locking:** Fixed pseudo-random seeds (`seed=42`) across bump evaluations to eliminate Monte Carlo variance noise during numerical differentiation.

### 5. Interactive Quantitative Risk Dashboard (Plotly)
1. **Payoff Profile & Current Value Curve:** Expiration intrinsic value vs. current theoretical options valuation across spot ranges.
2. **Lognormal Terminal PDF:** Probability density of underlying prices at expiry with target strike overlay.
3. **Comprehensive Greeks Sensitivity:** Delta, Gamma (100x), Vega, Theta, and Rho plotted across the underlying spot spectrum.
4. **Multi-Colored Monte Carlo Paths:** HSL-spectrum color-mapped asset trajectories highlighting distribution dispersion.
5. **Numerical Convergence Asymptote:** Model convergence benchmarks comparing Binomial Lattice steps ($N \in [10, 200]$) and Monte Carlo sample sizes ($M \in [100, 10000]$) against the analytical BSM baseline.

---

## 📂 Project Structure

```bash
├── data/
│   ├── __init__.py
│   ├── market_data_laout.py    # MarketDataLayout container
│   └── market_data.py          # yfinance data ingestion 
├── models/
│   ├── __init__.py
│   ├── black_scholes.py        # Analytical BSM model & closed-form Greeks
│   ├── binomial_tree.py        # CRR Binomial Tree lattice model (American/European)
│   └── monte_carlo.py          # Vectorized GBM Monte Carlo simulation engine
├── utils/
│   ├── __init__.py
│   ├── greeks.py               # Bump-and-revalue finite difference Greek calculator
│   ├── implied_vol.py          # Brent's method root-finding IV calibrator
│   └── charts.py               # 5-Panel interactive Plotly dashboard generator
├── main.py                     # Primary terminal execution pipeline
├── requirements.txt            # Environment dependencies
└── README.md                   # Project documentation

```

---

## 🛠️ Installation & Setup

### Prerequisites

* Python 3.9+ installed.

### 1. Clone the Repository

```bash
git clone [https://github.com/amrit1610-fin/Option-Pricing-Terminal](https://github.com/amrit1610-fin/Option-Pricing-Terminal)
cd options-pricing-engine

```

### 2. Create and Activate a Virtual Environment

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

#### `requirements.txt`

```text
numpy
scipy
yfinance
plotly

```

---

## 💻 Execution & Sample Output

Run the terminal pipeline from your console:

```bash
python main.py

```

### CLI Terminal Session

```text
======================================================================
               INSTITUTIONAL OPTIONS PRICING TERMINAL                 
======================================================================
Enter Ticker (e.g., ^SPX, AAPL) [default: AAPL]: NVDA
Enter Expiration (YYYY-MM-DD) [default: 2026-09-18]: 2026-09-18
Enter Target Strike [default: 225.0]: 130.0
Option Type (call/put) [default: call]: call

[*] Fetching live market data for NVDA via yfinance...
[*] Calibrating True Implied Volatility from Market Premium...

----------------------------------------------------------------------
                       CONTRACT SPECIFICATIONS                        
----------------------------------------------------------------------
 Underlying Spot: $128.50
 Target Strike:   $130.00
 Time to Expiry:  0.0658 Years
 Market Premium:  $6.45
 True Implied IV: 48.20%
 Exercise Style:  AMERICAN
----------------------------------------------------------------------

[*] Initializing Pricing Engines...

======================================================================
                   VALUATION & SENSITIVITY MATRIX                     
======================================================================
METRIC          | BSM             | BINOMIAL        | MONTE CARLO    
----------------------------------------------------------------------
PRICE           | 6.4500          | 6.4582          | 6.4410         
DELTA           | 0.5148          | 0.5160          | 0.5132         
GAMMA           | 0.0245          | 0.0246          | 0.0241         
THETA           | -0.0912         | -0.0908         | -0.0915        
VEGA            | 0.1280          | 0.1278          | 0.1284         
RHO             | 0.0385          | 0.0386          | 0.0381         

[*] Generating Data Visualization Dashboard...
[SUCCESS] Rendering interactive dashboard in browser...
======================================================================

```

---

## 📊 Quantitative Dashboard Visuals

When execution finishes, an interactive dark-themed Plotly dashboard will automatically launch:

* **Top Left:** Expiration Payoff profile overlaid with current continuous valuation curve.
* **Top Right:** Terminal probability distribution with underlying moneyness bounds.
* **Middle Left:** Dynamic sensitivity curves across Spot ($S$) for all primary first- and second-order Greeks.
* **Middle Right:** Vectorized Monte Carlo sample trajectories with distinct HSL color gradients.
* **Bottom Panel:** Multi-tier model convergence analysis demonstrating algorithmic stability.

---


## Author:

**[Amritanshu Kumar Singh](https://github.com/amrit1610-fin)** | Quantitative Researcher 
