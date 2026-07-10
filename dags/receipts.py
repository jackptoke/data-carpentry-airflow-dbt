"""Ingestion layer: land raw receipt JSON into DuckDB.

This is the single source-loading step of the pipeline. It reads every receipt
JSON file in the data directory using DuckDB's native ``read_json`` (which
preserves the nested struct/list structure) and (re)creates the
``main.raw_receipts`` landing table that the dbt project consumes as its source.

Producing this asset triggers the ``dbt_receipts_analytics`` DAG (see dags/dbt.py),
which transforms ``raw_receipts`` into the staging/intermediate/mart models.
"""
from __future__ import annotations

import logging
from pathlib import Path

import duckdb
from airflow.sdk import asset

log = logging.getLogger(__name__)

# Resolve paths from the repo root so the task never depends on the worker CWD.
# In the container this is /opt/airflow; locally it is the repository root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_GLOB = PROJECT_ROOT / "data" / "receipts" / "*.json"
DUCKDB_PATH = PROJECT_ROOT / "dbt" / "receipts_analytics" / "receipts.duckdb"


@asset(schedule="@daily", uri="duckdb://main/raw_receipts")
def raw_receipts() -> None:
    """Load all receipt JSON files into the ``main.raw_receipts`` table."""
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    log.info("Loading receipts from %s into %s", DATA_GLOB, DUCKDB_PATH)

    with duckdb.connect(str(DUCKDB_PATH)) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS main;")
        conn.execute(
            """
            CREATE OR REPLACE TABLE main.raw_receipts AS
            SELECT * FROM read_json(?, format = 'auto', union_by_name = true)
            """,
            [str(DATA_GLOB)],
        )
        row_count = conn.execute(
            "SELECT COUNT(*) FROM main.raw_receipts"
        ).fetchone()[0]

    log.info("Loaded %s receipts into main.raw_receipts", row_count)
    if row_count == 0:
        raise ValueError(
            f"No receipts were loaded from {DATA_GLOB}. "
            "Check that the data directory is populated and mounted."
        )
