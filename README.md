# NIFTYQuant Dashboard
https://niftyquant-eyq8nth9hjbjwpcajbqqjw.streamlit.app/
### NIFTY 50 Options Intelligence & Quantitative Decision-Support Terminal

NIFTYQuant is a quantitative options-analysis dashboard built for the NIFTY 50 derivatives market. It brings market data, volatility, option positioning, liquidity, Greeks, contract scoring, and multi-expiry analysis into a single decision-support environment.

The objective is simple: take a large and complex NIFTY option chain and turn it into a structured view that helps identify, compare, and evaluate potentially interesting contracts.

---

## Dashboard Overview

The main dashboard provides an immediate snapshot of the current NIFTY options environment.

It displays NIFTY spot, the ATM strike, implied volatility, realized historical volatility, Put-Call Ratio (PCR), and Volatility Risk Premium (VRP). The dashboard also provides a market-regime interpretation together with Buy Edge, Sell Edge, and an overall directional bias.

This allows the user to understand the broader volatility and positioning environment before looking at individual option contracts.

<img width="1882" height="930" alt="image" src="https://github.com/user-attachments/assets/5c623184-7b71-4b93-a1f4-fbdf8496af2c" />


---

## Market Regime & Signal Engine

The Market Regime & Signal Engine combines the quantitative measurements calculated by NIFTYQuant into a concise market read.

The system compares the current volatility environment and contract-level signals to identify whether the market is behaving in a more neutral, favorable, or cautionary configuration.

Buy Edge and Sell Edge highlight the strongest currently ranked opportunities, while the overall bias provides a high-level interpretation of the relative strength of those signals.

These signals are intended as **decision-support indicators**, not automatic trade recommendations.

---

## Trade Quality Matrix

The Trade Quality Matrix provides a detailed comparison of the highest-ranked option contracts.

Each contract can be evaluated using:

- Strike
- Option type
- LTP
- Implied volatility
- Historical volatility
- VRP
- Delta
- Open interest
- Volume
- Buy Edge
- Sell Edge
- Trade Quality Score (TQS)

This makes it possible to compare contracts using multiple quantitative characteristics instead of relying on a single metric.

For example, two contracts may have similar Buy Edge scores while having different TQS values because of differences in liquidity, spread, delta, open interest, volatility characteristics, or other scoring factors.

<img width="1857" height="815" alt="image" src="https://github.com/user-attachments/assets/5f6234b3-7dc6-4c26-bc7f-3ce84fb20281" />


---

## Implied Volatility Surface & Open Interest Structure

NIFTYQuant also provides visual tools for understanding the structure of the option chain.

The **Implied Volatility Surface** shows how implied volatility changes across strikes for calls and puts. This helps identify the shape of the volatility curve and areas where implied volatility is relatively elevated or compressed.

The **Open Interest Structure** shows call and put open interest across strikes. Large concentrations of open interest can highlight areas where market positioning is particularly significant.

These charts are designed to provide additional market context and should be interpreted together with spot price, volatility, liquidity, and contract-level metrics rather than used as standalone prediction tools.

<img width="1865" height="607" alt="image" src="https://github.com/user-attachments/assets/1fb85290-8f18-4750-8e12-fa9b0f8633de" />


---

## Multi-Expiry Analysis

NIFTYQuant is designed to analyze multiple future NIFTY expiries rather than focusing exclusively on the nearest expiry.

The refresh pipeline discovers available future expiries, retrieves the relevant option-chain data, calculates the required quantitative metrics, scores the contracts, and stores snapshots in SQLite.

This allows contracts from different expirations to be compared using the same analytical framework.

The result is a broader view of where potentially interesting opportunities exist across the NIFTY expiry curve.

---

## Volatility Risk Premium

NIFTYQuant uses the following definition for dashboard-level VRP:

`VRP = ATM IV - Historical Volatility`

Positive VRP means implied volatility is above the measured historical volatility.

Negative VRP means implied volatility is below the measured historical volatility.

VRP is used as one component of the broader volatility and contract-analysis framework.

---

## Buy Edge & Sell Edge

**Buy Edge** and **Sell Edge** are relative quantitative scores used to identify contracts with stronger characteristics from the corresponding buying or selling perspective.

A high Buy Edge does not automatically mean that an option should be purchased, and a high Sell Edge does not automatically mean that an option should be sold.

Instead, the scores help reduce a large option chain into a smaller set of contracts that deserve closer analysis.

---

## Trade Quality Score

**Trade Quality Score (TQS)** provides an overall quality assessment of an option contract based on the quantitative characteristics used by NIFTYQuant.

TQS allows contracts with different strikes and option types to be compared on a common scale.

This becomes particularly useful when two contracts have similar Buy Edge or Sell Edge scores but differ in other characteristics such as liquidity, spread, delta, open interest, or volatility.

---

## From Raw Market Data to Decision Support

The NIFTYQuant workflow can be summarized as:

```text
Market Data
     ↓
Option-Chain Parsing
     ↓
Implied Volatility & Greeks
     ↓
Historical Volatility
     ↓
VRP Analysis
     ↓
Liquidity & Spread Analysis
     ↓
Contract Scoring
     ↓
Trade Quality Ranking
     ↓
Multi-Expiry Comparison
     ↓
NIFTYQuant Dashboard

## Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your Upstox access token as `UPSTOX_ACCESS_TOKEN` (never commit it).

Refresh data:

```bash
python main.py
```

Run dashboard:

```bash
streamlit run niftyquant_dashboard_pro_multi_expiry_refresh.py
```

Validate stored data:

```bash
python validate_niftyquant.py
```

## VRP

Dashboard summary VRP is `ATM IV - Historical Volatility`.

Contract VRP is also based on `IV - HV`; negative VRP indicates IV below realized volatility and positive VRP indicates IV above realized volatility.

## Project layout

- `main.py` — multi-expiry data refresh and scoring pipeline
- `niftyquant_dashboard_pro_multi_expiry_refresh.py` — Streamlit dashboard
- `engine/` — pricing, IV, volatility, scoring and ranking
- `upstox/` — market-data retrieval/parsing
- `database/` — SQLite snapshot persistence

## Security

API tokens, `.env` files, SQLite databases, caches, checkpoints, and backups are excluded from Git.

## Disclaimer

NIFTYQuant is a research and decision-support tool, not investment advice. Options trading involves substantial risk.
