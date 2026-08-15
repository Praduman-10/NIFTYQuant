import numpy as np
from scipy.stats import norm

MIN_T = 1e-6
MIN_SIGMA = 1e-6


def _safe_T(T):
    return max(T, MIN_T)


def _safe_sigma(sigma):
    return max(sigma, MIN_SIGMA)


def d1(S, K, T, r, sigma, q=0.0):
    T = _safe_T(T)
    sigma = _safe_sigma(sigma)
    return (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))


def d2(S, K, T, r, sigma, q=0.0):
    return d1(S, K, T, r, sigma, q) - sigma * np.sqrt(_safe_T(T))


def call_price(S, K, T, r, sigma, q=0.0):
    T = _safe_T(T)
    D1, D2 = d1(S, K, T, r, sigma, q), d2(S, K, T, r, sigma, q)
    return S * np.exp(-q * T) * norm.cdf(D1) - K * np.exp(-r * T) * norm.cdf(D2)


def put_price(S, K, T, r, sigma, q=0.0):
    T = _safe_T(T)
    D1, D2 = d1(S, K, T, r, sigma, q), d2(S, K, T, r, sigma, q)
    return K * np.exp(-r * T) * norm.cdf(-D2) - S * np.exp(-q * T) * norm.cdf(-D1)


def price(S, K, T, r, sigma, option_type, q=0.0):
    option_type = option_type.lower()
    if option_type in ("c", "call", "ce"):
        return call_price(S, K, T, r, sigma, q)
    if option_type in ("p", "put", "pe"):
        return put_price(S, K, T, r, sigma, q)
    raise ValueError(f"Unknown option_type: {option_type}")


def vega(S, K, T, r, sigma, q=0.0):
    T = _safe_T(T)
    D1 = d1(S, K, T, r, sigma, q)
    return S * np.exp(-q * T) * norm.pdf(D1) * np.sqrt(T)


def greeks(S, K, T, r, sigma, option_type, q=0.0):
    option_type = option_type.lower()
    T = _safe_T(T)
    sigma = _safe_sigma(sigma)
    D1, D2 = d1(S, K, T, r, sigma, q), d2(S, K, T, r, sigma, q)
    is_call = option_type in ("c", "call", "ce")
    gamma_ = np.exp(-q * T) * norm.pdf(D1) / (S * sigma * np.sqrt(T))
    vega_ = vega(S, K, T, r, sigma, q) / 100.0
    if is_call:
        delta_ = np.exp(-q * T) * norm.cdf(D1)
        theta_ = (-S * np.exp(-q*T) * norm.pdf(D1) * sigma/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(D2) + q*S*np.exp(-q*T)*norm.cdf(D1)) / 365.0
        rho_ = K*T*np.exp(-r*T)*norm.cdf(D2)/100.0
        prob_itm = norm.cdf(D2)
    else:
        delta_ = -np.exp(-q*T) * norm.cdf(-D1)
        theta_ = (-S*np.exp(-q*T)*norm.pdf(D1)*sigma/(2*np.sqrt(T)) + r*K*np.exp(-r*T)*norm.cdf(-D2) - q*S*np.exp(-q*T)*norm.cdf(-D1)) / 365.0
        rho_ = -K*T*np.exp(-r*T)*norm.cdf(-D2)/100.0
        prob_itm = norm.cdf(-D2)
    return {"delta": delta_, "gamma": gamma_, "vega": vega_, "theta": theta_, "rho": rho_, "prob_itm": prob_itm}


def prob_to_decimal_odds(prob, floor=1e-4):
    prob = min(max(prob, floor), 1 - floor)
    return 1.0 / prob
