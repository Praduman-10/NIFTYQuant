import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def historical_volatility(prices: pd.Series, window: int = 20, annualize: bool = True) -> pd.Series:
    log_returns = np.log(prices / prices.shift(1))
    rolling_std = log_returns.rolling(window=window).std()
    return rolling_std * np.sqrt(TRADING_DAYS_PER_YEAR) if annualize else rolling_std


def multi_window_hv(prices: pd.Series, windows=(10, 20, 30)) -> pd.DataFrame:
    return pd.DataFrame({f"hv_{w}d": historical_volatility(prices, w) for w in windows})


def iv_rank(current_iv: float, iv_history: pd.Series) -> float:
    lo, hi = iv_history.min(), iv_history.max()
    if hi - lo < 1e-9:
        return 50.0
    return float(np.clip((current_iv - lo) / (hi - lo) * 100, 0, 100))


def iv_percentile(current_iv: float, iv_history: pd.Series) -> float:
    if len(iv_history) == 0:
        return 50.0
    return float((iv_history < current_iv).mean() * 100)
