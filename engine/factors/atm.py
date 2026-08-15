def apply(df, spot):
    df = df.copy()
    distance = abs(df["strike"] - spot) / spot
    df["factor_atm"] = (100 - distance * 2000).clip(0, 100)
    return df
