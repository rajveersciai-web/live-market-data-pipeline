import requests
import sqlite3
import time
from datetime import datetime

# 1. EXTRACT: Pull live top 10 USD market assets with 24h percentage change
url = "https://api.coingecko.com/api/v3/coins/markets"
params = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 10,
    "page": 1
}

raw_coins = None
for attempt in range(1, 4):
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw_coins = response.json()
        print(f"LIVE API SUCCESS (Attempt {attempt}): Downloaded {len(raw_coins)} assets.\n")
        break
    except Exception as error:
        print(f"Attempt {attempt} failed: {error}")
        if attempt < 3:
            time.sleep(2)

if not raw_coins:
    print("ALERT: Live API unreachable. Stopping safely.")
    exit(1)

# 2. WAREHOUSE LOAD: Store historical time-series snapshots (never overwrite history!)
conn = sqlite3.connect("revenue.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS price_history (
    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    name TEXT,
    price_usd REAL,
    market_cap_usd INTEGER,
    change_24h_pct REAL,
    captured_at TEXT
)
""")

snapshot_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for coin in raw_coins:
    cursor.execute("""
    INSERT INTO price_history (symbol, name, price_usd, market_cap_usd, change_24h_pct, captured_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        coin["symbol"].upper().strip(),
        coin["name"].strip(),
        float(coin["current_price"] or 0),
        int(coin["market_cap"] or 0),
        round(float(coin["price_change_percentage_24h"] or 0), 2),
        snapshot_time
    ))

conn.commit()

# 3. SQL ANALYTICS LAYER: Generate executive insights directly in SQL
print("=== TOP 3 GAINERS / MOVERS (24H %) ===")
cursor.execute("""
SELECT symbol, name, price_usd, change_24h_pct
FROM price_history
WHERE captured_at = ?
ORDER BY change_24h_pct DESC
LIMIT 3
""", (snapshot_time,))
for row in cursor.fetchall():
    print(f" {row[0]} ({row[1]}): ${row[2]:,.2f} | 24h Change: {row[3]}%")

print("\n=== MARKET DOMINANCE SHARE (%) ===")
cursor.execute("""
SELECT 
    symbol,
    ROUND((market_cap_usd * 100.0) / (SELECT SUM(market_cap_usd) FROM price_history WHERE captured_at = ?), 2) AS dominance_pct
FROM price_history
WHERE captured_at = ?
ORDER BY dominance_pct DESC
LIMIT 5
""", (snapshot_time, snapshot_time))
for row in cursor.fetchall():
    print(f" {row[0]}: {row[1]}% of Top-10 Market Cap")

cursor.execute("SELECT COUNT(*) FROM price_history")
total_rows = cursor.fetchone()[0]
print(f"\nSUCCESS: Historical snapshot saved! Total historical rows in warehouse: {total_rows}")

conn.close()
