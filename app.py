# ── app.py — MPT Portfolio Optimizer ─────────────────────────────────────────

import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import streamlit as st
from datetime import date

# ── Page Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MPT Portfolio Optimizer",
    page_icon="📊",
    layout="wide"
)

# ── Header ────────────────────────────────────────────────────────────────────

st.title("📊 MPT Portfolio Optimizer")
st.markdown("Built on **Modern Portfolio Theory (Markowitz, 1952)** — enter any set of US or Indian stocks to generate the efficient frontier and identify optimal portfolio allocations.")

st.warning("""
**Important:** This tool supports **either** US stocks/ETFs **or** Indian stocks/ETFs (NSE/BSE) in a single run.  
Do **not** mix both — currency differences (USD vs INR) will produce misleading results.  
Indian stocks: append **.NS** (NSE) or **.BO** (BSE) — e.g. `RELIANCE.NS`, `HDFCBANK.NS`
""")

st.markdown("---")
st.subheader("⚙️ Configuration")

# ── Row 1: Tickers ────────────────────────────────────────────────────────────

tickers_input = st.text_input(
    "Enter tickers (comma separated)",
    placeholder="e.g. AAPL, MSFT, AMZN  or  TCS.NS, RELIANCE.NS, INFY.NS",
    help="US stocks/ETFs: AAPL, MSFT, GLD | Indian stocks (NSE): RELIANCE.NS, HDFCBANK.NS"
)

# ── Row 2: Risk-free rate and Simulation count ────────────────────────────────

col1, col2 = st.columns(2)

with col1:
    risk_free_input = st.number_input(
    "Annual risk-free rate (%)",
    min_value=0.0,
    max_value=20.0,
    value=None,
    placeholder="e.g. 4.25",
    step=0.25,
    help="Use 3-month T-bill rate for US portfolios (~5.25%) or RBI repo rate for Indian portfolios (~6.25%)"
)

risk_free_rate = risk_free_input / 100 if risk_free_input is not None else None

with col2:
    num_portfolios = st.select_slider(
        "Number of simulated portfolios",
        options=[5000, 10000, 15000, 20000, 25000, 30000],
        value=10000
    )

# ── Row 3: Date range ─────────────────────────────────────────────────────────

col3, col4 = st.columns(2)

with col3:
    start_date = st.date_input("Start date", value=date(2022, 1, 1))

with col4:
    end_date = st.date_input("End date", value=date.today())

st.markdown("---")

run_button = st.button("🚀 Run Optimization", use_container_width=True)

# ── Main Logic ────────────────────────────────────────────────────────────────

if run_button:

    # Validate inputs
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    if len(tickers) < 2:
        st.error("❌ Please enter at least 2 tickers.")
        st.stop()

    if risk_free_rate is None:
        st.error("❌ Please enter an annual risk-free rate.")
        st.stop()
    
    if end_date <= start_date:
        st.error("❌ End date must be after start date.")
        st.stop()

    # ── Download Data ─────────────────────────────────────────────────────────

    with st.spinner("⏳ Downloading price data..."):
        try:
            raw_data = yf.download(tickers, start=start_date, end=end_date, auto_adjust=True)
            prices   = raw_data["Close"].dropna()
            returns  = prices.pct_change().dropna()

            if returns.empty:
                st.error("❌ No data returned. Check your tickers and date range.")
                st.stop()

            returns = returns.dropna(axis=1, how="all")
            tickers = list(returns.columns)

            if len(tickers) < 2:
                st.error("❌ Not enough valid tickers after data download. Please check your inputs.")
                st.stop()

        except Exception as e:
            st.error(f"❌ Data download failed: {e}")
            st.stop()

    # ── Compute Statistics ────────────────────────────────────────────────────

    mean_returns = returns.mean() * 252
    cov_matrix   = returns.cov() * 252
    n_assets     = len(tickers)

    # ── Monte Carlo Simulation ────────────────────────────────────────────────

    with st.spinner(f"⏳ Simulating {num_portfolios:,} portfolios..."):
        port_returns    = np.zeros(num_portfolios)
        port_volatility = np.zeros(num_portfolios)
        port_sharpe     = np.zeros(num_portfolios)
        port_weights    = np.zeros((num_portfolios, n_assets))

        for i in range(num_portfolios):
            weights            = np.random.random(n_assets)
            weights            = weights / weights.sum()
            p_return           = np.dot(weights, mean_returns)
            p_volatility       = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            p_sharpe           = (p_return - risk_free_rate) / p_volatility
            port_returns[i]    = p_return
            port_volatility[i] = p_volatility
            port_sharpe[i]     = p_sharpe
            port_weights[i]    = weights

    # ── Identify Optimal Portfolios ───────────────────────────────────────────

    # Max Sharpe
    max_sharpe_idx        = np.argmax(port_sharpe)
    max_sharpe_return     = float(port_returns[max_sharpe_idx])
    max_sharpe_volatility = float(port_volatility[max_sharpe_idx])
    max_sharpe_ratio      = float(port_sharpe[max_sharpe_idx])
    max_sharpe_weights    = port_weights[max_sharpe_idx]

    # Min Volatility
    min_vol_idx        = np.argmin(port_volatility)
    min_vol_return     = float(port_returns[min_vol_idx])
    min_vol_volatility = float(port_volatility[min_vol_idx])
    min_vol_sharpe     = float(port_sharpe[min_vol_idx])
    min_vol_weights    = port_weights[min_vol_idx]

    # Max Return — calculated directly
    best_asset_idx                     = np.argmax(mean_returns.values)
    max_return_weights                 = np.zeros(n_assets)
    max_return_weights[best_asset_idx] = 1.0
    max_return_return                  = float(mean_returns.iloc[best_asset_idx])
    max_return_volatility              = float(np.sqrt(cov_matrix.iloc[best_asset_idx, best_asset_idx]))
    max_return_sharpe                  = float((max_return_return - risk_free_rate) / max_return_volatility)

    # ── Plotly Chart ──────────────────────────────────────────────────────────

    y_min     = min(float(port_returns.min()), float(min_vol_return), float(max_sharpe_return), float(max_return_return))
    y_max     = max(float(port_returns.max()), float(min_vol_return), float(max_sharpe_return), float(max_return_return))
    y_padding = (y_max - y_min) * 0.1
    
    x_min     = min(float(port_volatility.min()), float(min_vol_volatility), float(max_sharpe_volatility), float(max_return_volatility))
    x_max     = max(float(port_volatility.max()), float(min_vol_volatility), float(max_sharpe_volatility), float(max_return_volatility))
    x_padding = (x_max - x_min) * 0.1

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=port_volatility, y=port_returns,
        mode="markers",
        marker=dict(size=4, color=port_sharpe, colorscale="Viridis",
                    colorbar=dict(title="Sharpe Ratio"), opacity=0.5),
        text=[f"Return: {r:.2%}<br>Volatility: {v:.2%}<br>Sharpe: {s:.4f}"
              for r, v, s in zip(port_returns, port_volatility, port_sharpe)],
        hoverinfo="text", name="Simulated Portfolios", showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=[max_sharpe_volatility], y=[max_sharpe_return],
        mode="markers",
        marker=dict(size=18, color="#2ECC71", symbol="circle", line=dict(color="white", width=1.5)),
        hovertext=[f"<b>Max Sharpe</b><br>Return: {max_sharpe_return:.2%}<br>"
                   f"Volatility: {max_sharpe_volatility:.2%}<br>Sharpe: {max_sharpe_ratio:.4f}<br><br>"
                   f"Weights:<br>" + "<br>".join([f"{t}: {w:.2%}" for t, w in zip(tickers, max_sharpe_weights)])],
        hoverinfo="text", name="Max Sharpe"
    ))

    fig.add_trace(go.Scatter(
        x=[min_vol_volatility], y=[min_vol_return],
        mode="markers",
        marker=dict(size=18, color="#3498DB", symbol="circle", line=dict(color="white", width=1.5)),
        hovertext=[f"<b>Min Volatility</b><br>Return: {min_vol_return:.2%}<br>"
                   f"Volatility: {min_vol_volatility:.2%}<br>Sharpe: {min_vol_sharpe:.4f}<br><br>"
                   f"Weights:<br>" + "<br>".join([f"{t}: {w:.2%}" for t, w in zip(tickers, min_vol_weights)])],
        hoverinfo="text", name="Min Volatility"
    ))

    fig.add_trace(go.Scatter(
        x=[max_return_volatility], y=[max_return_return],
        mode="markers",
        marker=dict(size=18, color="#E74C3C", symbol="circle", line=dict(color="white", width=1.5)),
        hovertext=[f"<b>Max Return</b><br>Return: {max_return_return:.2%}<br>"
                   f"Volatility: {max_return_volatility:.2%}<br>Sharpe: {max_return_sharpe:.4f}<br><br>"
                   f"Weights:<br>" + "<br>".join([f"{t}: {w:.2%}" for t, w in zip(tickers, max_return_weights)])],
        hoverinfo="text", name="Max Return"
    ))

    fig.update_layout(
        title=dict(text="Efficient Frontier — Modern Portfolio Theory", font=dict(size=22)),
        xaxis=dict(title="Annualised Volatility (Risk)", tickformat=".1%",
                   fixedrange=True, range=[x_min - x_padding, x_max + x_padding]),
        yaxis=dict(title="Annualised Return", tickformat=".1%",
                   fixedrange=True, range=[y_min - y_padding, y_max + y_padding]),
        legend=dict(x=0.99, y=0.01, xanchor = "right", yanchor = "bottom", bgcolor="rgba(255,255,255,0.1)"),
        hovermode="closest", height=600, template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True, config=dict(scrollZoom=False))

    # ── Summary Tables ────────────────────────────────────────────────────────

    st.subheader("📋 Optimal Portfolio Summary")

    metrics_df = pd.DataFrame({
        "Metric":         ["Annualised Return", "Annualised Volatility", "Sharpe Ratio"],
        "Max Sharpe":     [f"{max_sharpe_return:.2%}", f"{max_sharpe_volatility:.2%}", f"{max_sharpe_ratio:.4f}"],
        "Min Volatility": [f"{min_vol_return:.2%}", f"{min_vol_volatility:.2%}", f"{min_vol_sharpe:.4f}"],
        "Max Return":     [f"{max_return_return:.2%}", f"{max_return_volatility:.2%}", f"{max_return_sharpe:.4f}"]
    })

    weights_df = pd.DataFrame({
        "Ticker":                tickers,
        "Max Sharpe Weight":     [f"{w:.2%}" for w in max_sharpe_weights],
        "Min Volatility Weight": [f"{w:.2%}" for w in min_vol_weights],
        "Max Return Weight":     [f"{w:.2%}" for w in max_return_weights]
    })

    st.dataframe(metrics_df, use_container_width=True, hide_index=True)
    st.dataframe(weights_df, use_container_width=True, hide_index=True)

    # ── Footer Disclaimer ─────────────────────────────────────────────────────

    st.markdown("---")
    st.caption("⚠️ This tool is for educational purposes only and does not constitute financial advice. Returns are based on historical data and past performance does not guarantee future results.")
