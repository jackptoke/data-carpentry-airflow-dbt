"""Build the local DuckDB with the ``main.raw_receipts`` landing table.

Mirrors the Airflow ingestion asset (``dags/receipts.py``) so the dbt project
can be built locally or in CI without running Airflow:

    python scripts/build_local_db.py
    cd dbt/receipts_analytics && dbt build --target dev --profiles-dir .
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DATA_GLOB = ROOT / "data" / "receipts" / "*.json"
DUCKDB_PATH = ROOT / "dbt" / "receipts_analytics" / "receipts.duckdb"


def main() -> None:
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(DUCKDB_PATH)) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS main;")
        conn.execute(
            """
            CREATE OR REPLACE TABLE main.raw_receipts AS
            SELECT * FROM read_json(?, format = 'auto', union_by_name = true)
            """,
            [str(DATA_GLOB)],
        )
        rows = conn.execute("SELECT COUNT(*) FROM main.raw_receipts").fetchone()[0]
    print(f"Loaded {rows} receipts into {DUCKDB_PATH}")
    if rows == 0:
        raise SystemExit(f"No receipts loaded from {DATA_GLOB}")


if __name__ == "__main__":
    main()
