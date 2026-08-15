import os

ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN", "")

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}",
}

UNDERLYING = "NSE_INDEX|Nifty 50"
RISK_FREE_RATE = 0.065
DIVIDEND_YIELD = 0.012
SNAPSHOT_INTERVAL = 60
SAVE_FOLDER = "snapshots"
