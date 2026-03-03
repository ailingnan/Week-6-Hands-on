"""
scheduler.py
------------
Scheduled Automated Data Ingestion Workflow
- Scans for new CSV files in the ./ingest_inbox/ directory
- Automatically parses and writes to Snowflake DOC_CHUNKS_FEATURED table (Append mode)
- Records ingestion logs to the INGEST_LOG table
- Can be run independently (python scheduler.py) or called by app.py
"""

import os
import time
import glob
import hashlib
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

load_dotenv()

# Paths are relative to project root when run via app.py (Streamlit),
# but may be relative to ingestion/ when run directly.
# We anchor them to project root by resolving based on this file location.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))

INBOX_DIR = os.path.join(PROJECT_ROOT, "ingest_inbox")
DONE_DIR = os.path.join(PROJECT_ROOT, "ingest_done")

# SQL for creating the Ingestion Log table
DDL_LOG = """
CREATE TABLE IF NOT EXISTS INGEST_LOG (
    INGEST_ID       VARCHAR(64)   NOT NULL,
    FILE_NAME       VARCHAR(512),
    FILE_HASH       VARCHAR(64),
    ROWS_INGESTED   INTEGER,
    STATUS          VARCHAR(16),
    ERROR_MSG       VARCHAR(2000),
    INGESTED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (INGEST_ID)
);
"""

REQUIRED_COLS = {"DOC_NAME", "PAGE_NUM", "CHUNK_ID", "CHUNK_TEXT", "TEXT_LENGTH"}


def sf_connect():
    # Try reading rsa_key.p8 from project root first; fallback to current working dir
    key_path_root = os.path.join(PROJECT_ROOT, "rsa_key.p8")
    key_path_cwd = os.path.join(os.getcwd(), "rsa_key.p8")
    key_path = key_path_root if os.path.exists(key_path_root) else key_path_cwd

    with open(key_path, "rb") as f:
        pk = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )

    pkb = pk.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=pkb,
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def ensure_dirs():
    """Ensure required local directories exist."""
    os.makedirs(INBOX_DIR, exist_ok=True)
    os.makedirs(DONE_DIR, exist_ok=True)


def ensure_log_table():
    """Ensure the ingestion log table exists in Snowflake."""
    conn = sf_connect()
    try:
        conn.cursor().execute(DDL_LOG)
        conn.commit()
    finally:
        conn.close()


def file_hash(path: str) -> str:
    """Generate MD5 hash for a file to detect duplicates."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def already_ingested(fhash: str) -> bool:
    """Check if a file with the same hash has been successfully ingested."""
    sql = "SELECT COUNT(*) FROM INGEST_LOG WHERE FILE_HASH=%s AND STATUS='success'"
    conn = sf_connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, (fhash,))
        return cur.fetchone()[0] > 0
    finally:
        conn.close()


def write_log(ingest_id, fname, fhash, rows, status, error=""):
    """Write an entry to the Snowflake INGEST_LOG table."""
    sql = """
    INSERT INTO INGEST_LOG
      (INGEST_ID, FILE_NAME, FILE_HASH, ROWS_INGESTED, STATUS, ERROR_MSG)
    VALUES (%s,%s,%s,%s,%s,%s)
    """
    conn = sf_connect()
    try:
        conn.cursor().execute(sql, (ingest_id, fname, fhash, rows, status, error))
        conn.commit()
    finally:
        conn.close()


def ingest_csv(path: str) -> dict:
    """Reads a CSV and appends data to DOC_CHUNKS_FEATURED."""
    fname = os.path.basename(path)
    fhash = file_hash(path)
    ingest_id = f"ing-{int(time.time())}-{fhash[:8]}"

    ensure_log_table()

    if already_ingested(fhash):
        return {"file": fname, "status": "skipped", "reason": "already ingested"}

    try:
        df = pd.read_csv(path)

        # Standardize column names to uppercase
        df.columns = [c.strip().upper() for c in df.columns]

       df = pd.read_csv(path)

# Standardize column names to uppercase
df.columns = [c.strip().upper() for c in df.columns]

if "CHUNK_TEXT" in df.columns:
    df["TEXT_LENGTH"] = df["CHUNK_TEXT"].fillna("").str.len()
else:
    raise ValueError("CSV is missing the 'CHUNK_TEXT' column")
        # Keep required columns only and clean
        df = df[list(REQUIRED_COLS)].copy()
        df = df.dropna(subset=["CHUNK_TEXT"])
        df["CHUNK_TEXT"] = df["CHUNK_TEXT"].astype(str)
        df["TEXT_LENGTH"] = df["CHUNK_TEXT"].str.len()

        conn = sf_connect()
        try:
            cur = conn.cursor()
            sql = """
            INSERT INTO DOC_CHUNKS_FEATURED
              (DOC_NAME, PAGE_NUM, CHUNK_ID, CHUNK_TEXT, TEXT_LENGTH)
            VALUES (%s,%s,%s,%s,%s)
            """

            rows = []
            for _, r in df.iterrows():
                rows.append(
                    (
                        str(r["DOC_NAME"]),
                        int(r["PAGE_NUM"]),
                        str(r["CHUNK_ID"]),
                        str(r["CHUNK_TEXT"]),
                        int(r["TEXT_LENGTH"]),
                    )
                )

            cur.executemany(sql, rows)
            conn.commit()
        finally:
            conn.close()

        write_log(ingest_id, fname, fhash, len(df), "success")

        # Move file to the processed directory
        done_path = os.path.join(DONE_DIR, fname)
        os.replace(path, done_path)

        return {"file": fname, "status": "success", "rows": len(df)}

    except Exception as e:
        write_log(ingest_id, fname, fhash, 0, "fail", str(e))
        return {"file": fname, "status": "fail", "error": str(e)}


def run_once() -> list:
    """Scans inbox, processes all CSVs, and returns result list."""
    ensure_dirs()
    files = glob.glob(os.path.join(INBOX_DIR, "*.csv"))
    if not files:
        return []

    results = []
    for f in files:
        results.append(ingest_csv(f))
    return results


def load_ingest_log(limit: int = 50) -> pd.DataFrame:
    """Retrieves ingestion logs for dashboard display."""
    ensure_log_table()
    sql = f"""
    SELECT INGEST_ID, FILE_NAME, ROWS_INGESTED, STATUS, ERROR_MSG, INGESTED_AT
    FROM INGEST_LOG
    ORDER BY INGESTED_AT DESC
    LIMIT {int(limit)}
    """
    conn = sf_connect()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return pd.DataFrame(rows, columns=cols)
    finally:
        conn.close()


# ---- Standalone Execution Mode (Polling) ----
if __name__ == "__main__":
    POLL_INTERVAL = int(os.getenv("SCHEDULER_INTERVAL_SEC", "60"))
    print(f"[Scheduler] Started, scanning {INBOX_DIR}/ every {POLL_INTERVAL}s")
    while True:
        results = run_once()
        for r in results:
            print(f"  [{datetime.utcnow().isoformat()}] {r}")
        time.sleep(POLL_INTERVAL)
