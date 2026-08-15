import requests
from datetime import datetime

from config import HEADERS, UNDERLYING

CONTRACTS_URL = "https://api.upstox.com/v2/option/contract"
OPTION_CHAIN_URL = "https://api.upstox.com/v2/option/chain"


def get_available_expiries():
    response = requests.get(CONTRACTS_URL, headers=HEADERS, params={"instrument_key": UNDERLYING})
    response.raise_for_status()
    contracts = response.json()["data"]
    return sorted(set(contract["expiry"] for contract in contracts))


def get_nearest_expiry():
    today = datetime.today().date()
    expiries = get_available_expiries()
    valid = [datetime.strptime(e, "%Y-%m-%d").date() for e in expiries if datetime.strptime(e, "%Y-%m-%d").date() >= today]
    return min(valid).strftime("%Y-%m-%d")


def fetch_option_chain():
    expiry = get_nearest_expiry()
    response = requests.get(OPTION_CHAIN_URL, headers=HEADERS, params={"instrument_key": UNDERLYING, "expiry_date": expiry})
    response.raise_for_status()
    return response.json()["data"]
