import numpy as np
import pandas as pd


def calculate_tqs(df: pd.DataFrame, spot: float) -> pd.DataFrame:
    df = df.copy()
    df["atm_distance_pct"] = (df["strike"] - spot).abs() / spot * 100
    df["atm_score"] = (100 - df["atm_distance_pct"] * 20).clip(lower=0, upper=100)
    liquidity = np.log1p(df["oi"]) + np.log1p(df["volume"])
    liquidity = (liquidity - liquidity.min()) / (liquidity.max() - liquidity.min() + 1e-9)
    df["liquidity_score"] = liquidity * 100
    df["spread_score"] = (100 - df["bid_ask_spread_pct"] * 1000).clip(lower=0)
    df["delta_score"] = (100 - abs(abs(df["delta"]) - 0.40) * 250).clip(lower=0)
    df["trade_quality"] = (
        0.35 * df["buy_edge_score"] +
        0.25 * df["liquidity_score"] +
        0.15 * df["atm_score"] +
        0.10 * df["spread_score"] +
        0.15 * df["delta_score"]
    )
    return df.sort_values("trade_quality", ascending=False)
