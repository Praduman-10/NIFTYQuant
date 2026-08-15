import numpy as np
from engine.black_scholes import price, vega, MIN_SIGMA

DEFAULT_MAX_ITER = 100
DEFAULT_TOL = 1e-6


def implied_vol_newton(market_price, S, K, T, r, option_type, q=0.0, sigma_init=0.25, tol=DEFAULT_TOL, max_iter=DEFAULT_MAX_ITER):
    sigma = sigma_init
    for i in range(max_iter):
        model_price = price(S, K, T, r, sigma, option_type, q)
        diff = model_price - market_price
        if abs(diff) < tol:
            return max(sigma, MIN_SIGMA), True, i + 1
        v = vega(S, K, T, r, sigma, q)
        if v < 1e-8:
            break
        sigma_new = sigma - diff / v
        if not np.isfinite(sigma_new) or sigma_new <= 0 or sigma_new > 5.0:
            break
        if abs(sigma_new - sigma) < tol:
            return max(sigma_new, MIN_SIGMA), True, i + 1
        sigma = sigma_new
    iv, converged, iters = implied_vol_bisection(market_price, S, K, T, r, option_type, q)
    return iv, converged, max_iter + iters


def implied_vol_bisection(market_price, S, K, T, r, option_type, q=0.0, lo=1e-4, hi=5.0, tol=1e-4, max_iter=200):
    p_lo = price(S, K, T, r, lo, option_type, q) - market_price
    p_hi = price(S, K, T, r, hi, option_type, q) - market_price
    if p_lo * p_hi > 0:
        return float("nan"), False, 0
    for i in range(max_iter):
        mid = 0.5 * (lo + hi)
        p_mid = price(S, K, T, r, mid, option_type, q) - market_price
        if abs(p_mid) < tol or (hi - lo) < tol:
            return mid, True, i + 1
        if p_lo * p_mid <= 0:
            hi = mid
        else:
            lo = mid
            p_lo = p_mid
    return 0.5 * (lo + hi), False, max_iter


def implied_vol(market_price, S, K, T, r, option_type, q=0.0, sigma_init=0.25):
    iv, _, _ = implied_vol_newton(market_price, S, K, T, r, option_type, q, sigma_init)
    return iv
