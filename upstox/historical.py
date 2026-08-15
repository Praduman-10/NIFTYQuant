import requests
import pandas as pd

from config import HEADERS, UNDERLYING

HISTORICAL_URL = "https://api.upstox.com/v2/historical-candle/{instrument}/{interval}/{to_date}/{from_date}"


def get_daily_closes(from_date, to_date):
    url = HISTORICAL_URL.format(
        instrument=UNDERLYING,
        interval="day",
        to_date=to_date,
        from_date=from_date,
    )
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    candles = response.json()["data"]["candles"]
    df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume", "oi"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df.set_index("datetime")["close"].sort_index()
