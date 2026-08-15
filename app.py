from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = Path("database/niftyquant.db")
TABLE = "option_snapshots"

st.set_page_config(page_title="NIFTYQuant Pro", page_icon="📊", layout="wide")
st.title("NIFTYQuant Pro")
st.caption("NIFTY 50 Options Intelligence Terminal")

if not DB_PATH.exists():
    st.error(f"Database file not found: {DB_PATH}")
    st.stop()

with sqlite3.connect(DB_PATH) as conn:
    df = pd.read_sql(f"SELECT * FROM {TABLE}", conn)

if df.empty:
    st.warning("No option-chain data is currently stored in SQLite.")
    st.stop()

for col in ["expiry", "as_of"]:
    df[col] = pd.to_datetime(df[col], errors="coerce")

expiries = sorted(df["expiry"].dropna().dt.strftime("%Y-%m-%d").unique())
selected = st.sidebar.selectbox("EXPIRY", expiries)
limit = st.sidebar.slider("CONTRACTS", 5, 20, 10, 5)
min_tqs = st.sidebar.slider("MIN TRADE QUALITY", 0, 100, 0, 5)

snapshot = df[df["expiry"] == pd.Timestamp(selected)].copy()
latest = snapshot["as_of"].max()
snapshot = snapshot[snapshot["as_of"] == latest]
snapshot = snapshot[snapshot["trade_quality"].fillna(0) >= min_tqs]

spot = float(snapshot["spot"].iloc[0])
atm = float(snapshot.loc[(snapshot["strike"] - spot).abs().idxmin(), "strike"])
ce_oi = snapshot.loc[snapshot["option_type"] == "CE", "oi"].sum()
pe_oi = snapshot.loc[snapshot["option_type"] == "PE", "oi"].sum()
pcr = pe_oi / ce_oi if ce_oi else 0
atm_rows = snapshot[snapshot["strike"] == atm]
atm_iv = atm_rows["iv"].median()
hv = snapshot["hv"].median()
vrp = atm_iv - hv

cols = st.columns(5)
for col, (label, value) in zip(cols, [("NIFTY SPOT", f"{spot:,.2f}"), ("ATM IV", f"{atm_iv:.2f}%"), ("HV", f"{hv:.2f}%"), ("PCR", f"{pcr:.2f}"), ("VRP", f"{vrp:+.2f}%")]):
    col.metric(label, value)

st.subheader("Top Buy Opportunities")
st.dataframe(snapshot.sort_values("buy_edge_score", ascending=False).head(limit), use_container_width=True, hide_index=True)
st.subheader("Top Sell Opportunities")
st.dataframe(snapshot.sort_values("sell_edge_score", ascending=False).head(limit), use_container_width=True, hide_index=True)

st.subheader("IV Surface")
iv = snapshot.dropna(subset=["iv"]).groupby(["strike", "option_type"])["iv"].mean().unstack(fill_value=0).sort_index()
st.line_chart(iv)

st.subheader("Open Interest")
oi = snapshot.groupby(["strike", "option_type"])["oi"].sum().unstack(fill_value=0).sort_index()
st.bar_chart(oi)
