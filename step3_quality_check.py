import sqlite3

# Connect to our historical warehouse
conn = sqlite3.connect("revenue.db")
cursor = conn.cursor()

print("=== RUNNING AUTOMATED DATA QUALITY CHECKS ===\n")

# CHECK 1: Verify the warehouse is not empty
cursor.execute("SELECT COUNT(*) FROM price_history")
total_rows = cursor.fetchone()[0]
assert total_rows > 0, "FAIL: price_history table is completely empty!"
print(f"[PASS] Check 1 — Warehouse Row Count: {total_rows} valid rows found.")

# CHECK 2: Verify zero missing or $0.00 prices exist
cursor.execute("SELECT COUNT(*) FROM price_history WHERE price_usd IS NULL OR price_usd <= 0")
invalid_prices = cursor.fetchone()[0]
assert invalid_prices == 0, f"FAIL: Found {invalid_prices} rows with missing or zero USD price!"
print("[PASS] Check 2 — Price Integrity: 0 missing or $0.00 prices detected.")

# CHECK 3: Verify latest snapshot batch contains all 10 assets
cursor.execute("""
SELECT captured_at, COUNT(*) as asset_count
FROM price_history
GROUP BY captured_at
ORDER BY captured_at DESC
LIMIT 1
""")
latest_batch = cursor.fetchone()
latest_time = latest_batch[0]
latest_count = latest_batch[1]

assert latest_count == 10, f"FAIL: Expected 10 assets in latest snapshot, got {latest_count}!"
print(f"[PASS] Check 3 — Snapshot Completeness: Latest batch ({latest_time}) has all {latest_count} assets.")

conn.close()
print("\nALL QUALITY GATES PASSED: Warehouse data is verified and ready for executive dashboards!")