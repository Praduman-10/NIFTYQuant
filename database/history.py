import sqlite3
import pandas as pd

DB_NAME = "database/niftyquant.db"


def save_snapshot(df: pd.DataFrame):
    conn = sqlite3.connect(DB_NAME)
    df.to_sql("option_snapshots", conn, if_exists="append", index=False)
    conn.close()
    print("Snapshot saved to SQLite.")
