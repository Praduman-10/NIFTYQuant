import pandas as pd


def option_chain_to_dataframe(chain):
    rows = []
    for strike_data in chain:
        expiry = strike_data.get("expiry")
        strike = strike_data.get("strike_price")
        spot = strike_data.get("underlying_spot_price")
        pcr = strike_data.get("pcr")

        for option_key, option_type in (("call_options", "CE"), ("put_options", "PE")):
            option = strike_data.get(option_key, {})
            market = option.get("market_data", {})
            greeks = option.get("option_greeks", {})
            rows.append({
                "instrument_key": option.get("instrument_key"),
                "strike": strike,
                "option_type": option_type,
                "expiry": expiry,
                "spot": spot,
                "pcr": pcr,
                "ltp": market.get("ltp", 0),
                "oi": market.get("oi", 0),
                "prev_oi": market.get("prev_oi", 0),
                "oi_change": market.get("oi", 0) - market.get("prev_oi", 0),
                "volume": market.get("volume", 0),
                "bid": market.get("bid_price", 0),
                "bid_qty": market.get("bid_qty", 0),
                "ask": market.get("ask_price", 0),
                "ask_qty": market.get("ask_qty", 0),
                "close": market.get("close_price", 0),
                "delta": greeks.get("delta", 0),
                "gamma": greeks.get("gamma", 0),
                "theta": greeks.get("theta", 0),
                "vega": greeks.get("vega", 0),
                "iv": greeks.get("iv", 0),
                "pop": greeks.get("pop", 0),
            })

    df = pd.DataFrame(rows)
    numeric_columns = ["strike", "spot", "pcr", "ltp", "oi", "prev_oi", "oi_change", "volume", "bid", "bid_qty", "ask", "ask_qty", "close", "delta", "gamma", "theta", "vega", "iv", "pop"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.fillna(0, inplace=True)
    df.sort_values(by=["expiry", "strike", "option_type"], inplace=True)
    return df.reset_index(drop=True)
