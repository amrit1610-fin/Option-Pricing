# Quantitative Option Pricing & Risk Analytics Terminal

[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Deployment](https://img.shields.io/badge/Deployed-Vercel%20%26%20Render-blue?style=flat-square)](https://vercel.com)
[![License](https://img.shields.io/badge/License-MIT-amber?style=flat-square)](LICENSE)

An institutional-grade quantitative finance web terminal inspired by Bloomberg DES/PRC interfaces. The engine prices European and American equity/index options across multiple mathematical frameworks, solves for implied volatility numerically, and calculates full first- and second-order risk sensitivities (Greeks).

---

## Architecture Overview

The system is architected as a decoupled, high-performance quantitative pipeline:


```

┌─────────────────────────────────────────────────────────────┐
│                    Next.js (Vercel)                        │
│   • Bloomberg CRT UI Theme (Tailwind CSS)                   │
│   • Dynamic Execution Logging System                       │
│   • Interactive Plotly Financial Visualizations            │
└──────────────────────────────┬──────────────────────────────┘
│ HTTPS / JSON API
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI (Render)                        │
│   • Auto-Routing Valuation Engine                           │
│   • Numerical Greeks Engine (Bump & Revalue)                │
│   • Alpaca Market Data Provider (OCC Symbol Encoding)       │
└──────────────────────────────┬──────────────────────────────┘
│
┌──────────────────┼──────────────────┐
▼                  ▼                  ▼
[Black-Scholes]   [Binomial Tree]    [Monte Carlo]
(European Closed) (American CRR/JR)  (Stochastic GBM)

```

---

## Core Features

### 1. Multi-Model Valuation Engine
* **Black-Scholes-Merton Engine:** Analytical closed-form pricing for European-style vanilla contracts.
* **Binomial Tree Engine (CRR / Jarrow-Rudd):** Lattice model supporting backward induction for early exercise evaluation in American-style contracts.
* **Monte Carlo Engine:** Geometric Brownian Motion (GBM) simulation running thousands of stochastic price paths with antithetic variance reduction and 95% confidence intervals.
* **Automatic Exercise-Style Routing:** Automatically detects whether an underlying instrument is European-settled (e.g., `SPX`, `NDX`, `RUT`, `VIX`) or American-settled (e.g., `NVDA`, `AAPL`, `SPY`) and routes execution to valid engines.

### 2. Risk Sensitivities (Numerical Greeks)
Calculated via central finite-difference approximation (bump-and-revalue) across all active models:
* **$\Delta$ (Delta):** $\frac{\partial V}{\partial S}$ — Directional spot sensitivity.
* **$\Gamma$ (Gamma):** $\frac{\partial^2 V}{\partial S^2}$ — Second-order convexity.
* **$\Theta$ (Theta):** $-\frac{\partial V}{\partial t}$ — Daily time decay.
* **$\mathcal{V}$ (Vega):** $\frac{\partial V}{\partial \sigma}$ — Volatility sensitivity.
* **$\rho$ (Rho):** $\frac{\partial V}{\partial r}$ — Interest rate sensitivity.

### 3. Quantitative Visualizations
* **Expiration Payoff Curve:** Terminal dollar payoff profile across varying spot prices.
* **Probability Curve:** In-the-money (ITM) cumulative distribution profile across strike ranges.
* **Greeks Profiling:** Multi-strike Greek sensitivity curves.
* **Model Convergence:** Binomial tree step convergence and Monte Carlo confidence band progression against the Black-Scholes benchmark.
* **Stochastic Paths:** Multi-trajectory Geometric Brownian Motion path simulation.

---

## Tech Stack

* **Frontend:** Next.js (App Router), React, Tailwind CSS, Plotly.js (`react-plotly.js`).
* **Backend:** FastAPI, Uvicorn, NumPy, SciPy, Pydantic.
* **Market Data API:** Alpaca Markets REST API (Paper Trading environment).
* **Infrastructure:** Vercel (Frontend Hosting), Render (Python Container Hosting).

---

## Project Structure


```

├── data/
│   ├── market_data.py          # Alpaca API client & OCC symbol encoder
│   └── market_data_layout.py   # Standardized dataclass container
├── models/
│   ├── black_scholes.py        # Analytical closed-form engine
│   ├── binomial_tree.py        # Lattice early-exercise engine
│   └── monte_carlo.py          # Stochastic path simulation engine
├── utils/
│   ├── greeks.py               # Numerical finite-difference solver
│   └── implied_vol.py          # Newton-Raphson / Brent IV root-finder
├── frontend/
│   ├── app/
│   │   ├── layout.tsx          # Terminal layout wrapper
│   │   └── page.tsx            # Main dashboard UI
│   ├── components/
│   │   └── TerminalChart.tsx   # Dynamic Plotly visualization component
│   └── package.json
├── main.py                     # FastAPI application endpoints
├── requirements.txt            # Python dependencies
├── vercel.json                 # Vercel deployment configuration
└── README.md

```

---

## Local Development Setup

### 1. Prerequisites
* Python 3.10+
* Node.js 18+ and npm
* Free [Alpaca Markets](https://alpaca.markets/) account (Paper Trading API keys)

### 2. Backend Setup
```bash
# Clone the repository
git clone [https://github.com/amrit1610-fin/Option-Pricing-Terminal](https://github.com/amrit1610-fin/Option-Pricing-Terminal)
cd option-pricing-terminal

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set your API credentials
export ALPACA_API_KEY="your_alpaca_key_id"
export ALPACA_SECRET_KEY="your_alpaca_secret_key"
# On Windows PowerShell:
# $env:ALPACA_API_KEY="your_alpaca_key_id"
# $env:ALPACA_SECRET_KEY="your_alpaca_secret_key"

# Start the FastAPI server
uvicorn main:app --reload --port 8000

```

### 3. Frontend Setup

```bash
# In a new terminal, navigate to the frontend directory
cd frontend

# Install node dependencies
npm install

# Configure local API endpoint
echo "NEXT_PUBLIC_API_URL=[http://127.0.0.1:8000](http://127.0.0.1:8000)" > .env.local

# Run the Next.js development server
npm run dev

```

Open [http://localhost:3000](http://localhost:3000) in your browser to access the terminal.

---

## Production Deployment

### Backend (Render)

1. Create a **New Web Service** linked to your GitHub repository.
2. Set the **Build Command** to: `pip install -r requirements.txt`
3. Set the **Start Command** to: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. In **Environment Variables**, add:
* `ALPACA_API_KEY`
* `ALPACA_SECRET_KEY`
* `PYTHON_VERSION` = `3.11.0`



### Frontend (Vercel)

1. Import the repository on [Vercel](https://vercel.com).
2. Set the **Root Directory** to `frontend`.
3. Set the **Framework Preset** to `Next.js`.
4. Add the environment variable:
* `NEXT_PUBLIC_API_URL` = `https://your-render-backend-url.onrender.com`


5. Click **Deploy**.

---

## Author:

**Amritanshu Kumar Singh**
Quantitative Researcher 
```