import numpy as np

def apply(df, spot):
    df = df.copy()
    liquidity = np.log1p(df["oi"]) + np.log1p(df["volume"])
    liquidity = (liquidity - liquidity.min()) / (liquidity.max() - liquidity.min() + 1e-9)
    df["factor_liquidity"] = liquidity * 100
    return df
