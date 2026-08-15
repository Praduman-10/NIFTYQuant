from __future__ import annotations

from datetime import date, datetime, timedelta
import requests
import pandas as pd

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
    r = requests.get(CONTRACTS_URL, headers=HEADERS, params={"instrument_key": UNDERLYING}, timeout=20)
    r.raise_for_status()
    return sorted({c["expiry"] for c in r.json().get("data", []) if c.get("expiry")})


def select_expiries(expiries, horizon_days=HORIZON_DAYS):
    today = date.today()
    cutoff = today + timedelta(days=horizon_days)
    selected = []
    for text in expiries:
        try:
            d = datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            continue
        if today <= d <= cutoff:
            selected.append(text)
    return selected


def fetch_option_chain_for_expiry(expiry):
    r = requests.get(OPTION_CHAIN_URL, headers=HEADERS, params={"instrument_key": UNDERLYING, "expiry_date": expiry}, timeout=20)
    r.raise_for_status()
    return r.json().get("data", [])


def main():
    engine = OptionsScoringEngine()
    history = get_daily_closes(
        from_date=(date.today() - timedelta(days=90)).strftime("%Y-%m-%d"),
        to_date=date.today().strftime("%Y-%m-%d"),
    )
    engine.seed_daily_history(history)
    snapshot_time = pd.Timestamp.now()
    expiries = select_expiries(get_available_expiries())
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
            scored = engine.update(df, spot=spot, as_of=snapshot_time)
            scored = calculate_tqs(scored, spot)
            save_snapshot(scored)
            successful += 1
            total_rows += len(scored)
            print(f"{expiry}: OK — {len(scored)} contracts")
        except Exception as exc:
            failed += 1
            print(f"{expiry}: FAILED — {type(exc).__name__}: {exc}")
    print(f"Successful expiries : {successful}")
    print(f"Failed expiries     : {failed}")
    print(f"Contracts saved     : {total_rows}")
    print(f"Snapshot timestamp  : {snapshot_time}")


if __name__ == "__main__":
    main()
