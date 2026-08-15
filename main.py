from __future__ import annotations

from datetime import date, datetime, timedelta
import pandas as pd
import requests

from config import HEADERS, UNDERLYING
from upstox.parser import option_chain_to_dataframe
from upstox.historical import get_daily_closes
from engine.scoring_engine import OptionsScoringEngine
from engine.quality_score import calculate_tqs
from database.history import save_snapshot

CONTRACTS_URL = "https://api.upstox.com/v2/option/contract"
OPTION_CHAIN_URL = "https://api.upstox.com/v2/option/chain"
HORIZON_DAYS = 90


def get_available_expiries():
    response = requests.get(CONTRACTS_URL, headers=HEADERS, params={"instrument_key": UNDERLYING}, timeout=20)
    response.raise_for_status()
    return sorted({c["expiry"] for c in response.json().get("data", []) if c.get("expiry")})


def get_future_expiries(expiries):
    today = date.today()
    cutoff = today + timedelta(days=HORIZON_DAYS)
    selected = []
    for expiry in expiries:
        try:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
        except ValueError:
            continue
        if today < expiry_date <= cutoff:
            selected.append(expiry)
    return selected


def fetch_option_chain_for_expiry(expiry):
    response = requests.get(OPTION_CHAIN_URL, headers=HEADERS, params={"instrument_key": UNDERLYING, "expiry_date": expiry}, timeout=20)
    response.raise_for_status()
    return response.json().get("data", [])


def main():
    engine = OptionsScoringEngine()
    history = get_daily_closes(
        from_date=(date.today() - timedelta(days=90)).strftime("%Y-%m-%d"),
        to_date=date.today().strftime("%Y-%m-%d"),
    )
    engine.seed_daily_history(history)
    refresh_time = pd.Timestamp.now()
    expiries = get_future_expiries(get_available_expiries())
    successful = failed = total_rows = 0

    for expiry in expiries:
        try:
            chain = fetch_option_chain_for_expiry(expiry)
            if not chain:
                failed += 1
                continue
            df = option_chain_to_dataframe(chain)
            if df.empty:
                failed += 1
                continue
            spot = float(df["spot"].iloc[0])
            scored = engine.update(df, spot=spot, as_of=refresh_time)
            scored = calculate_tqs(scored, spot)
            save_snapshot(scored)
            successful += 1
            total_rows += len(scored)
            print(f"{expiry}: OK — {len(scored)} contracts | Spot {spot:,.2f}")
        except Exception as exc:
            failed += 1
            print(f"{expiry}: FAILED — {type(exc).__name__}: {exc}")

    print(f"Successful expiries : {successful}")
    print(f"Failed expiries     : {failed}")
    print(f"Contracts saved     : {total_rows}")
    print(f"Refresh timestamp   : {refresh_time}")


if __name__ == "__main__":
    main()
