from pathlib import Path
import html
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = Path("database/niftyquant.db")
TABLE = "option_snapshots"

st.set_page_config(page_title="NIFTYQuant Pro", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp { background:#050505; color:#f5f5f5; }
.block-container { max-width:1700px; padding-top:4.8rem !important; padding-bottom:2rem; }
[data-testid="stSidebar"] { background:#080808; border-right:1px solid #242424; }
.nq-brand { font-size:2.35rem; font-weight:900; letter-spacing:-1.8px; }
.nq-kicker { color:#777; font-size:.7rem; font-weight:800; letter-spacing:1.7px; margin-bottom:3px; }
.nq-sub { color:#777; font-size:.82rem; margin-top:4px; }
.live { border:1px solid #303030; border-radius:999px; padding:7px 12px; color:#aaa; font-size:.7rem; font-weight:800; }
.dot { color:#00e676; }
.card { background:linear-gradient(145deg,#151515,#0a0a0a); border:1px solid #292929; border-radius:14px; padding:16px; min-height:100px; }
.label { color:#858585; font-size:.67rem; font-weight:800; letter-spacing:1px; }
.value { color:#fff; font-size:1.65rem; font-weight:900; margin-top:8px; }
.sub { color:#666; font-size:.68rem; margin-top:3px; }
.panel { background:linear-gradient(145deg,#111,#080808); border:1px solid #252525; border-radius:15px; padding:18px; margin:12px 0 18px; }
.panel-title { color:#fff; font-size:.82rem; font-weight:900; letter-spacing:1px; text-transform:uppercase; margin-bottom:12px; }
.signal { background:#0b0b0b; border:1px solid #252525; border-radius:11px; padding:13px; min-height:78px; }
.signal-label { color:#777; font-size:.64rem; font-weight:800; letter-spacing:.8px; text-transform:uppercase; }
.signal-value { color:#fff; font-size:1.05rem; font-weight:900; margin-top:5px; }
.green { color:#00e676 !important; } .red { color:#ff5252 !important; } .amber { color:#ffc107 !important; }
.section { color:#fff; font-size:.86rem; font-weight:900; letter-spacing:1px; text-transform:uppercase; margin:4px 0 10px; }
.hint { color:#555; font-size:.65rem; float:right; text-transform:none; letter-spacing:0; }
.trade { background:#0d0d0d; border:1px solid #272727; border-radius:12px; padding:13px 14px; margin:7px 0; }
.trade-top { display:flex; justify-content:space-between; align-items:center; }
.strike { color:#fff; font-size:1rem; font-weight:900; }
.type { color:#777; font-size:.68rem; margin-left:5px; }
.score { font-size:1.15rem; font-weight:900; }
.meta { color:#7d7d7d; font-size:.66rem; margin-top:4px; }
.grid { display:grid; grid-template-columns:repeat(4,1fr); gap:7px; margin-top:9px; padding-top:9px; border-top:1px solid #202020; }
.stat-l { color:#5f5f5f; font-size:.58rem; text-transform:uppercase; }
.stat-v { color:#d7d7d7; font-size:.69rem; font-weight:800; margin-top:2px; }
.read { color:#8a8a8a; font-size:.64rem; margin-top:9px; }
</style>
""", unsafe_allow_html=True)

def fmt_compact(x):
    x = float(x or 0)
    if abs(x) >= 1_000_000: return f"{x/1_000_000:.2f}M"
    if abs(x) >= 1_000: return f"{x/1_000:.1f}K"
    return f"{x:,.0f}"

def card(label, value, sub=""):
    return f'<div class="card"><div class="label">{html.escape(label)}</div><div class="value">{html.escape(value)}</div><div class="sub">{html.escape(sub)}</div></div>'

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
for col in ["strike","ltp","iv","hv","vrp","delta","oi","volume","bid_ask_spread_pct","spot","buy_edge_score","sell_edge_score","trade_quality"]:
    if col in df.columns: df[col] = pd.to_numeric(df[col], errors="coerce")

st.sidebar.markdown('<div style="font-size:1.25rem;font-weight:900;color:#fff;">NIFTYQuant</div><div style="color:#666;font-size:.68rem;margin-bottom:22px;">OPTIONS INTELLIGENCE TERMINAL</div>', unsafe_allow_html=True)
expiries = sorted(df["expiry"].dropna().dt.strftime("%Y-%m-%d").unique())
selected = st.sidebar.selectbox("EXPIRY", expiries, index=0)
limit = st.sidebar.slider("CONTRACTS", 5, 20, 10, 5)
min_tqs = st.sidebar.slider("MIN TRADE QUALITY", 0, 100, 90, 5)

snapshot = df[df["expiry"] == pd.Timestamp(selected)].copy()
latest = snapshot["as_of"].max()
latest_all = snapshot[snapshot["as_of"] == latest].copy()
if latest_all.empty:
    st.warning("No current snapshot is available for the selected expiry.")
    st.stop()

spot = float(latest_all["spot"].iloc[0])
atm = float(latest_all.loc[(latest_all["strike"] - spot).abs().idxmin(), "strike"])
atm_iv = float(latest_all[latest_all["strike"] == atm]["iv"].median())
hv = float(latest_all["hv"].median())
vrp = atm_iv - hv
ce_oi = float(latest_all.loc[latest_all["option_type"] == "CE", "oi"].sum())
pe_oi = float(latest_all.loc[latest_all["option_type"] == "PE", "oi"].sum())
pcr = pe_oi / ce_oi if ce_oi else 0
best_buy = float(latest_all["buy_edge_score"].max())
best_sell = float(latest_all["sell_edge_score"].max())
overall_bias = "BUY BIAS" if best_buy > best_sell else ("SELL BIAS" if best_sell > best_buy else "BALANCED")
if vrp >= 2: regime = "PREMIUM SELL / CAUTION"
elif vrp <= -2: regime = "LONG VOL BIAS"
elif pcr >= 1.2: regime = "PUT-SIDE SUPPORT"
elif pcr <= 0.8: regime = "CALL-SIDE PRESSURE"
else: regime = "NEUTRAL"
iv_state = "IV RICH" if vrp >= 2 else ("IV CHEAP" if vrp <= -2 else "IV NEUTRAL")
position_state = "PUT HEAVY" if pcr >= 1.2 else ("CALL HEAVY" if pcr <= .8 else "BALANCED")

# Header / eyebrow
c1, c2 = st.columns([5,1])
with c1:
    st.markdown('<div class="nq-kicker">NIFTY 50 - OPTIONS INTELLIGENCE</div><div class="nq-brand">NIFTYQuant Pro</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="nq-sub">Quantitative options decision-support terminal - Latest snapshot {latest.strftime("%d %b %Y %H:%M:%S")}</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div style="text-align:right;margin-top:15px"><span class="live"><span class="dot">●</span> LIVE ANALYTICS</span></div>', unsafe_allow_html=True)
st.divider()

kpis=[("NIFTY SPOT",f"{spot:,.2f}",f"ATM {atm:,.0f}"),("ATM IV",f"{atm_iv:.2f}%","Implied volatility"),("REALIZED HV",f"{hv:.2f}%","20D historical volatility"),("PCR",f"{pcr:.2f}",f"PE OI {fmt_compact(pe_oi)}"),("VRP",f"{vrp:+.2f}%","IV minus HV")]
cols=st.columns(5)
for col,item in zip(cols,kpis):
    with col: st.markdown(card(*item),unsafe_allow_html=True)

regime_class="green" if regime=="PUT-SIDE SUPPORT" else ("red" if regime=="CALL-SIDE PRESSURE" else "amber")
bias_class="green" if overall_bias=="BUY BIAS" else ("red" if overall_bias=="SELL BIAS" else "amber")
st.markdown('<div class="panel"><div class="panel-title">Market Regime & Signal Engine</div>',unsafe_allow_html=True)
sc=st.columns(4)
with sc[0]: st.markdown(f'<div class="signal"><div class="signal-label">Market regime</div><div class="signal-value {regime_class}">{regime}</div><div class="sub">{iv_state} | {position_state}</div></div>',unsafe_allow_html=True)
with sc[1]: st.markdown(f'<div class="signal"><div class="signal-label">Buy edge</div><div class="signal-value green">{best_buy:.1f}</div><div class="sub">Best current setup</div></div>',unsafe_allow_html=True)
with sc[2]: st.markdown(f'<div class="signal"><div class="signal-label">Sell edge</div><div class="signal-value red">{best_sell:.1f}</div><div class="sub">Best current setup</div></div>',unsafe_allow_html=True)
with sc[3]: st.markdown(f'<div class="signal"><div class="signal-label">Overall bias</div><div class="signal-value {bias_class}">{overall_bias}</div><div class="sub">Score spread based</div></div>',unsafe_allow_html=True)
st.markdown('</div>',unsafe_allow_html=True)

eligible=latest_all[latest_all["trade_quality"].fillna(0)>=min_tqs].copy()
def render_trade(row,score_col,side):
    score=float(row[score_col]); q=float(row["trade_quality"]); cls="green" if side=="BUY" else "red"
    vrp_txt=f'{row["vrp"]:+.2f}%' if pd.notna(row.get("vrp")) else "-"
    spread_txt=f'{row["bid_ask_spread_pct"]:.2f}%' if pd.notna(row.get("bid_ask_spread_pct")) else "-"
    read='IV below HV | delta in active zone' if side=="BUY" and row["vrp"]<0 else ('IV above HV' if row["vrp"]>0 else 'IV below HV')
    return f'''<div class="trade"><div class="trade-top"><div><div class="strike">{row["strike"]:,.0f} <span class="type">{row["option_type"]}</span></div><div class="meta">LTP Rs {row["ltp"]:,.2f} | IV {row["iv"]:.2f}% | HV {row["hv"]:.2f}%</div></div><div style="text-align:right"><div class="score {cls}">{score:.1f}</div><div class="meta">TQS {q:.1f}</div></div></div><div class="grid"><div><div class="stat-l">VRP</div><div class="stat-v">{vrp_txt}</div></div><div><div class="stat-l">Delta</div><div class="stat-v">{row["delta"]:+.2f}</div></div><div><div class="stat-l">OI</div><div class="stat-v">{fmt_compact(row["oi"])}</div></div><div><div class="stat-l">Spread</div><div class="stat-v">{spread_txt}</div></div></div><div class="read"><b>READ:</b> {read}</div></div>'''

left,right=st.columns(2)
with left:
    st.markdown('<div class="section">Top Long Opportunities <span class="hint">BUY EDGE</span></div>',unsafe_allow_html=True)
    buys=eligible.sort_values("buy_edge_score",ascending=False).head(limit)
    if buys.empty: st.info("No long opportunities meet the selected trade-quality threshold.")
    else: st.markdown("".join(render_trade(r,"buy_edge_score","BUY") for _,r in buys.iterrows()),unsafe_allow_html=True)
with right:
    st.markdown('<div class="section">Top Short Opportunities <span class="hint">SELL EDGE</span></div>',unsafe_allow_html=True)
    sells=eligible.sort_values("sell_edge_score",ascending=False).head(limit)
    if sells.empty: st.info("No short opportunities meet the selected trade-quality threshold.")
    else: st.markdown("".join(render_trade(r,"sell_edge_score","SELL") for _,r in sells.iterrows()),unsafe_allow_html=True)
st.divider()

left,right=st.columns(2)
with left:
    st.markdown('<div class="section">Implied Volatility Surface <span class="hint">CE / PE by strike</span></div>',unsafe_allow_html=True)
    iv=latest_all.dropna(subset=["iv"]).groupby(["strike","option_type"])["iv"].mean().unstack(fill_value=0).sort_index()
    st.line_chart(iv,height=340)
    st.caption(f"Spot: {spot:,.2f} | ATM strike: {atm:,.0f}")
with right:
    st.markdown('<div class="section">Open Interest Structure <span class="hint">CE / PE concentration</span></div>',unsafe_allow_html=True)
    oi=latest_all.groupby(["strike","option_type"])["oi"].sum().unstack(fill_value=0).sort_index()
    st.bar_chart(oi,height=340)
st.divider()

st.markdown('<div class="section">Trade Quality Matrix <span class="hint">Highest ranked contracts</span></div>',unsafe_allow_html=True)
matrix_cols=["strike","option_type","ltp","iv","hv","vrp","delta","oi","volume","buy_edge_score","sell_edge_score","trade_quality"]
matrix=latest_all.sort_values("trade_quality",ascending=False).head(20)[matrix_cols].copy()
matrix.columns=["STRIKE","TYPE","LTP","IV %","HV %","VRP %","DELTA","OI","VOLUME","BUY EDGE","SELL EDGE","TQS"]
st.dataframe(matrix,use_container_width=True,hide_index=True)
st.divider()

st.markdown('<div class="panel"><div class="panel-title">Current Market Read</div>',unsafe_allow_html=True)
read_text=("Options are trading above realized volatility, indicating a positive volatility risk premium in the current snapshot." if vrp>0 else "Options are trading below realized volatility, indicating a negative volatility risk premium in the current snapshot." if vrp<0 else "Implied and realized volatility are approximately aligned in the current snapshot.")
mc1,mc2=st.columns([2,1])
with mc1: st.markdown(f'<div style="font-size:1.15rem;font-weight:900;color:#fff;">{regime}</div><div style="color:#888;font-size:.75rem;line-height:1.6;margin-top:7px;">{read_text}</div>',unsafe_allow_html=True)
with mc2: st.markdown(f'<div style="color:#777;font-size:.7rem;">SPOT / ATM</div><div style="color:#fff;font-weight:900;margin-top:3px;">{spot:,.2f} / {atm:,.0f}</div><div style="color:#777;font-size:.7rem;margin-top:8px;">PCR / VRP</div><div style="color:#fff;font-weight:900;margin-top:3px;">{pcr:.2f} / {vrp:+.2f}%</div>',unsafe_allow_html=True)
st.markdown('</div>',unsafe_allow_html=True)
st.markdown(f'<div style="text-align:center;color:#444;font-size:.64rem;padding:16px 0;">NIFTYQuant Pro | Snapshot {latest.strftime("%Y-%m-%d %H:%M:%S")} | Quantitative decision-support only</div>',unsafe_allow_html=True)
