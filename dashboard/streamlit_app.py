"""Receipts Analytics dashboard — entry point.

Uses a single-page layout with a sidebar selector rather than st.navigation's
URL-based multipage routing. The routing variant flashes a spurious "Page not
found" dialog when the app is served behind Docker Desktop's port-forward proxy:
the added websocket latency lets the URL change and the rerun message race, so
the client-side router momentarily fails to resolve the new path. Rendering the
selected page in-place sidesteps routing entirely and behaves identically in
Docker, locally, and on Streamlit Community Cloud.
"""
import os
from pathlib import Path

import streamlit as st

from constants import DUCKDB_FILE

st.set_page_config(page_title="Receipts Analytics", layout="wide")


def _db_is_complete() -> bool:
    """True only if the warehouse exists *and* the final mart is present.

    Checking the final table (not just the file) catches a partial/corrupt DB.
    """
    db = Path(DUCKDB_FILE)
    if not db.exists():
        return False
    try:
        import duckdb

        with duckdb.connect(str(db), read_only=True) as con:
            (n,) = con.execute(
                "select count(*) from information_schema.tables "
                "where table_name = 'fct_business_kpis'"
            ).fetchone()
        return bool(n)
    except Exception:
        return False


def _require_database() -> None:
    """Ensure a prebuilt DuckDB warehouse is present before rendering.

    The dashboard is a read-only consumer — it never *builds* the warehouse,
    which keeps this image lean (no dbt/dbt-core dependency). The DB comes from:
      * Docker: ``DUCKDB_FILE`` points at the Airflow-written warehouse volume.
      * Everywhere else: a prebuilt ``dbt/receipts_analytics/receipts.duckdb`` is
        committed to the repo (and baked into the Railway image).
    If it's genuinely missing (e.g. deleted in local dev), point at the build.
    """
    if os.getenv("DUCKDB_FILE") or _db_is_complete():
        return
    st.error(
        "Analytics database not found. The dashboard serves a prebuilt "
        "`dbt/receipts_analytics/receipts.duckdb`. Rebuild it with "
        "`python scripts/build_local_db.py`, then "
        "`cd dbt/receipts_analytics && dbt deps && dbt build --profiles-dir .` — "
        "or run the Airflow pipeline."
    )
    st.stop()


_require_database()

# (section, label, script) — order defines sidebar order.
PAGES = [
    ("Overview", "Executive Summary", "executive_summary.py"),
    ("Analysis", "Seasonality of profit", "question1.py"),
    ("Analysis", "Customer loyalty", "question2.py"),
    ("Analysis", "Customer segments (RFM)", "customer_segments.py"),
    ("Analysis", "Product performance", "product_performance.py"),
    ("Analysis", "Employee turnover", "question3.py"),
]

with st.sidebar:
    st.markdown("## Receipts Analytics")
    st.caption("by Jack Toke")
    st.markdown("")
    labels = [label for _, label, _ in PAGES]
    # Show the section next to each option so the grouping is still visible.
    choice = st.radio(
        "Pages",
        labels,
        label_visibility="collapsed",
        captions=[section for section, _, _ in PAGES],
    )

script = next(script for _, label, script in PAGES if label == choice)

# Execute the selected page script in place. Each page is a plain top-to-bottom
# Streamlit script (imports `constants`, renders with `st.*`); running it here
# renders it into the current app on every rerun, exactly as a routed page would.
page_path = Path(__file__).resolve().parent / script
exec(compile(page_path.read_text(), script, "exec"), {"__name__": "__page__"})
