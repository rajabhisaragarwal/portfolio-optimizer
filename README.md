# 📊 MPT Portfolio Optimizer

A Python-based **Modern Portfolio Theory (MPT)** optimizer that constructs the efficient 
frontier for any user-defined set of US or Indian stocks and ETFs. Built as the third 
project in a quantitative finance portfolio series, completing the trilogy of 
**performance measurement → factor analysis → portfolio construction.**

---

## 📌 What This Project Does

Given a set of tickers and a date range, the optimizer:
- Downloads historical price data via `yfinance`
- Computes annualised historical returns and a full covariance matrix
- Runs a **Monte Carlo simulation** of 10,000 random portfolios to map the efficient frontier
- Identifies three optimal portfolios across the risk/return spectrum
- Visualizes results interactively via **Plotly** with hover-over portfolio details

---

## 📈 The Three Optimal Portfolios

| Portfolio | What It Optimizes | Best For |
|---|---|---|
| ⭐ **Max Sharpe Ratio** | Highest return per unit of risk | Most investors |
| 🔵 **Min Volatility** | Lowest possible portfolio risk | Conservative / risk-averse investors |
| 🔴 **Max Return** | Highest raw historical return | Aggressive investors |

> **Note:** The Max Return portfolio is calculated directly (not via simulation) and will 
> typically concentrate 100% in the single best performing asset — return is maximized 
> but diversification is fully sacrificed.

---

## 🖼️ Sample Output

![Optimized Portfolios](Monte Carlo Simulation.png)

---

## 🧠 Methodology

### Returns
Expected returns are computed as **annualised historical mean returns** — the average 
daily return scaled by 252 trading days. These are backward-looking estimates, not 
forward-looking forecasts.

### Risk
Portfolio volatility is derived from the **annualised covariance matrix** of daily returns. 
This captures both individual asset variance and cross-asset covariance — the mathematical 
foundation of MPT's diversification benefit.

### Optimization
- **Monte Carlo simulation** generates 10,000 random weight combinations, each summing to 
100%, to map the empirical efficient frontier
- **Max Sharpe** and **Min Volatility** portfolios are identified from the simulation results
- **Max Return** portfolio is solved directly via `numpy.argmax` on mean returns — not 
approximated via simulation — ensuring it always correctly identifies the highest returning 
single asset

### Sharpe Ratio
