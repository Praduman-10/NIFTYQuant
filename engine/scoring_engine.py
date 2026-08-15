from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pandas as pd

from engine.black_scholes import greeks, prob_to_decimal_odds
from engine.iv_solver import implied_vol_newton
from engine.volatility import historical_volatility, iv_rank, iv_percentile


def _years_to_expiry(as_of, expiry):
    expiry = pd.Timestamp(expiry)
    if expiry.time() == pd.Timestamp("00:00:00").time():
        expiry += pd.Timedelta(days=1)
    return max((expiry - pd.Timestamp(as_of)).total_seconds() / (365 * 24 * 3600), 1e-6)


def _minmax_scale(s):
    lo, hi = s.min(), s.max()
    if not np.isfinite(lo) or not np.isfinite(hi) or hi - lo < 1e-9:
        return pd.Series(50.0, index=s.index)
    return (s - lo) / (hi - lo) * 100


@dataclass
class EngineConfig:
    risk_free_rate: float = 0.065
    dividend_yield: float = 0.012
    hv_window_days: int = 20
    iv_history_maxlen: int = 500
    w_buy_vrp: float = 0.35
    w_buy_iv_rank: float = 0.20
    w_buy_gamma_vega: float = 0.20
    w_buy_theta_burden: float = 0.15
    w_buy_liquidity: float = 0.10
    w_sell_vrp: float = 0.35
    w_sell_iv_rank: float = 0.20
    w_sell_theta_collect: float = 0.25
    w_sell_vega_risk: float = 0.10
    w_sell_liquidity: float = 0.10


@dataclass
class OptionsScoringEngine:
    config: EngineConfig = field(default_factory=EngineConfig)
    _iv_history: dict = field(default_factory=dict)
    _daily_closes: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    _last_hv: Optional[float] = None

    def seed_daily_history(self, daily_closes):
        self._daily_closes = daily_closes.sort_index()
        self._recompute_hv()

    def append_daily_close(self, date, close):
        self._daily_closes.loc[pd.Timestamp(date)] = close
        self._daily_closes = self._daily_closes.sort_index()
        self._recompute_hv()

    def _recompute_hv(self):
        if len(self._daily_closes) < self.config.hv_window_days + 1:
            self._last_hv = None
            return
        value = historical_volatility(self._daily_closes, self.config.hv_window_days).iloc[-1]
        self._last_hv = float(value) if np.isfinite(value) else None

    def update(self, snapshot, spot, as_of=None):
        as_of = pd.Timestamp(as_of) if as_of is not None else pd.Timestamp.now()
        hv = self._last_hv
        rows = []
        for _, row in snapshot.iterrows():
            T = _years_to_expiry(as_of, row["expiry"])
            key = (row["strike"], row["option_type"], pd.Timestamp(row["expiry"]).date())
            otype = "call" if str(row["option_type"]).upper() in ("CE", "C", "CALL") else "put"
            iv, converged, iters = implied_vol_newton(row["ltp"], spot, row["strike"], T, self.config.risk_free_rate, otype, self.config.dividend_yield)
            if not np.isfinite(iv):
                continue
            hist = self._iv_history.setdefault(key, [])
            hist.append(iv)
            if len(hist) > self.config.iv_history_maxlen:
                hist.pop(0)
            hist_series = pd.Series(hist)
            g = greeks(spot, row["strike"], T, self.config.risk_free_rate, iv, otype, self.config.dividend_yield)
            bid = row.get("bid", np.nan); ask = row.get("ask", np.nan)
            spread = (ask - bid) / ask if pd.notna(ask) and ask else np.nan
            rows.append({
                "strike": row["strike"], "option_type": row["option_type"], "expiry": pd.Timestamp(row["expiry"]).date(),
                "T_years": T, "ltp": row["ltp"], "iv": iv, "iv_converged": converged, "iv_newton_iters": iters,
                "hv": hv, "vrp": iv - hv if hv is not None else np.nan,
                "iv_rank": iv_rank(iv, hist_series) if len(hist_series) > 1 else 50.0,
                "iv_percentile": iv_percentile(iv, hist_series) if len(hist_series) > 1 else 50.0,
                **g, "decimal_odds": prob_to_decimal_odds(g["prob_itm"]),
                "oi": row.get("oi", np.nan), "volume": row.get("volume", np.nan), "bid_ask_spread_pct": spread,
            })
        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df["spot"] = spot
        df["as_of"] = as_of
        return self._score(df)

    def _score(self, df):
        cfg = self.config
        vrp = df["vrp"].fillna(0)
        vrp_scaled = _minmax_scale(vrp)
        cheap_scaled = 100 - vrp_scaled
        iv_rank_scaled = df["iv_rank"].fillna(50)
        gamma_vega_scaled = _minmax_scale(df["gamma"].fillna(0) + df["vega"].fillna(0))
        theta_burden = (df["theta"].abs() / df["ltp"].replace(0, np.nan)).fillna(0)
        theta_burden_scaled = _minmax_scale(theta_burden)
        theta_collect_scaled = _minmax_scale(df["theta"].abs().fillna(0))
        vega_risk_scaled = _minmax_scale(df["vega"].abs().fillna(0))
        liquidity = _minmax_scale(df["oi"].fillna(0) * 0.5 + df["volume"].fillna(0) * 0.5)
        if df["bid_ask_spread_pct"].notna().any():
            spread_penalty = _minmax_scale(df["bid_ask_spread_pct"].fillna(df["bid_ask_spread_pct"].median()))
            liquidity = (liquidity + 100 - spread_penalty) / 2
        df["buy_edge_score"] = (cfg.w_buy_vrp*cheap_scaled + cfg.w_buy_iv_rank*(100-iv_rank_scaled) + cfg.w_buy_gamma_vega*gamma_vega_scaled + cfg.w_buy_theta_burden*(100-theta_burden_scaled) + cfg.w_buy_liquidity*liquidity).round(1)
        df["sell_edge_score"] = (cfg.w_sell_vrp*vrp_scaled + cfg.w_sell_iv_rank*iv_rank_scaled + cfg.w_sell_theta_collect*theta_collect_scaled + cfg.w_sell_vega_risk*(100-vega_risk_scaled) + cfg.w_sell_liquidity*liquidity).round(1)
        df["decimal_odds"] = df["decimal_odds"].round(2)
        df["iv"] = (df["iv"] * 100).round(2)
        if df["hv"].notna().any(): df["hv"] = (df["hv"] * 100).round(2)
        if df["vrp"].notna().any(): df["vrp"] = (df["vrp"] * 100).round(2)
        return df.sort_values("buy_edge_score", ascending=False).reset_index(drop=True)

    def top_setups(self, scored_df, side="buy", option_type=None, n=5):
        col = "buy_edge_score" if side == "buy" else "sell_edge_score"
        d = scored_df
        if option_type:
            d = d[d["option_type"].str.upper() == option_type.upper()]
        return d.sort_values(col, ascending=False).head(n)
