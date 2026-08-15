import pandas as pd


def filter_contracts(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()
    filtered = filtered.dropna(subset=["buy_edge_score", "sell_edge_score", "iv"])
    filtered = filtered[filtered["iv"] <= 200]
    filtered = filtered[filtered["oi"] >= 1000]
    filtered = filtered[filtered["volume"] > 0]
    return filtered


def top_buy(df: pd.DataFrame, n=10):
    return filter_contracts(df).sort_values("buy_edge_score", ascending=False).head(n)


def top_sell(df: pd.DataFrame, n=10):
    return filter_contracts(df).sort_values("sell_edge_score", ascending=False).head(n)
