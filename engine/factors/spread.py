def apply(df, spot):
    df = df.copy()
    df["factor_spread"] = (100 - df["bid_ask_spread_pct"] * 1000).clip(0, 100)
    return df
