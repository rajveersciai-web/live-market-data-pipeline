import requests
import sqlite3
import time
from datetime import datetime

# Real global REST API (CoinGecko live crypto market prices — 100% unblocked globally)
url = "https://api.coingecko.com/api/v3/coins/markets"
params = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 10,
    "page": 1
}

# 1. EXTRACT WITH AUTOMATIC RETRY
raw_coins = None
for attempt in range(1, 4):
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw_coins = response.json()
        print(f"LIVE API SUCCESS (Attempt {attempt}): Downloaded {len(raw_coins)} live market assets!\n")
        break
    except Exception as error:
        print(f"Attempt {attempt} failed: {error}")
        if attempt < 3:
            print("Retrying in 2 seconds...")
            time.sleep(2)

if not raw_coins:
    print("ALERT: Live API unreachable after 3 attempts. Pipeline stopped safely.")
    exit(1)

# 2. LOAD & TRANSFORM: Connect to SQL database and create table
conn = sqlite3.connect("revenue.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS market_assets (
    asset_id TEXT PRIMARY KEY,
    symbol TEXT,
    name TEXT,
    current_price_usd REAL,
    market_cap_usd INTEGER,
    ingested_at TEXT
)
""")

# 3. INSERT CLEANED RECORDS
for coin in raw_coins:
    cursor.execute("""
    INSERT OR REPLACE INTO market_assets (asset_id, symbol, name, current_price_usd, market_cap_usd, ingested_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        coin["id"],
        coin["symbol"].upper().strip(),
        coin["name"].strip(),
        float(coin["current_price"]),
        int(coin["market_cap"]),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

conn.commit()

# 4. VERIFY: Query the SQL table
cursor.execute("SELECT symbol, name, current_price_usd, market_cap_usd FROM market_assets LIMIT 5")
for row in cursor.fetchall():
    print(row)

conn.close()
print("\nSUCCESS: Live financial market data extracted, cleaned, and loaded into revenue.db!")
