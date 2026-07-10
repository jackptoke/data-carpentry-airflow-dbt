"""Shared configuration and data access for the Streamlit dashboard.

The dashboard is a read-only consumer of the DuckDB database produced by the
Airflow + dbt pipeline. All pages query through :func:`run_query`, which caches
results and opens the database read-only so it never contends with the pipeline
for the single DuckDB write lock.
"""
from pathlib import Path

import duckdb
import streamlit as st

# Resolve the DuckDB path from the repo root so it works both locally and in the
# container (WORKDIR /opt/airflow, dbt project mounted read-only).
DUCKDB_FILE = str(
    Path(__file__).resolve().parent.parent
    / "dbt" / "receipts_analytics" / "receipts.duckdb"
)

# Businesses in the dataset, in a stable display order.
BUSINESSES = [
    "Ed's Barber Supplies",
    "Penguin Swim School",
    "Please Bring Pizza Pronto",
    "Wake Up with Coffee",
]

# A consistent colour per business, reused across every chart.
BUSINESS_COLOURS = {
    "Ed's Barber Supplies": "#fb5607",
    "Penguin Swim School": "#ff006e",
    "Please Bring Pizza Pronto": "#8338ec",
    "Wake Up with Coffee": "#3a86ff",
}


@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str):
    """Run a read-only query and return a DataFrame (cached for 10 minutes)."""
    try:
        with duckdb.connect(DUCKDB_FILE, read_only=True) as conn:
            return conn.sql(sql).df()
    except (duckdb.IOException, duckdb.CatalogException) as exc:
        st.error(
            "Could not read the analytics database. Run the Airflow pipeline "
            f"first so the dbt models exist.\n\n```\n{exc}\n```"
        )
        st.stop()
