# Real-Time Financial Market ETL Pipeline

Automated Python data ingestion pipeline that extracts live USD market metrics via REST API with retry/backoff fault tolerance, standardizes fields, and loads idempotent records into SQL storage.

## Architecture & Key Features
- **Fault-Tolerant Extraction (`requests`):** Fetches live USD cryptocurrency pricing and market cap metrics with automatic retry loops and safe failure isolation so bad network states never corrupt downstream tables.
- **Data Transformation:** Standardizes ticker symbols, trims whitespace, and enforces strict numeric/timestamp schemas before loading.
- **Idempotent SQL Loading (`sqlite3`):** Uses `INSERT OR REPLACE` primary-key constraints so repeated pipeline runs update prices cleanly without creating duplicate records.

## How to Run Locally
```bash
pip install requests
python step1_fetch.py
