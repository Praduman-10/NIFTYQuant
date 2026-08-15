# NIFTYQuant

NIFTY 50 options intelligence terminal with a multi-expiry refresh pipeline, quantitative contract scoring, and a Streamlit dashboard.

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
