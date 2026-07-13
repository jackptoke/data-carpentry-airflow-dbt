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
import subprocess
import sys
from pathlib import Path

import streamlit as st

from constants import DUCKDB_FILE

st.set_page_config(page_title="Receipts Analytics", layout="wide")

ROOT = Path(__file__).resolve().parent.parent
DBT_PROJECT = ROOT / "dbt" / "receipts_analytics"


@st.cache_resource(show_spinner="Building the analytics database (first run only)…")
def _ensure_database() -> None:
    """Reconstruct the DuckDB warehouse when it isn't already present.

    In Docker the Airflow pipeline is the writer and sets ``DUCKDB_FILE`` on the
    dashboard, so we never self-build there. Standalone (e.g. Streamlit Community
    Cloud, where there is no Airflow), we rebuild from the committed raw JSON with
    the same two steps Airflow orchestrates — land the receipts, then run the dbt
    models. Cached so it happens once per container boot.
    """
    if os.getenv("DUCKDB_FILE"):
        return  # externally managed (Docker warehouse / Airflow)
    if Path(DUCKDB_FILE).exists():
        return  # already built (local dev, or a warm Cloud container)

    # 1. Land the raw JSON into main.raw_receipts (absolute output path).
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_local_db.py")],
        check=True,
        cwd=ROOT,
    )
    # 2. Build the dbt models. The dev profile's output path is relative
    #    (`receipts.duckdb`), so dbt must run from the project dir — exactly as
    #    the documented `cd dbt/receipts_analytics && dbt ...` workflow — or it
    #    would open a different, empty database.
    dbt_exe = Path(sys.executable).parent / "dbt"
    dbt = str(dbt_exe) if dbt_exe.exists() else "dbt"
    for args in (["deps"], ["run", "--target", "dev", "--profiles-dir", "."]):
        subprocess.run([dbt, *args], check=True, cwd=DBT_PROJECT)


_ensure_database()

# (section, label, script) — order defines sidebar order.
PAGES = [
    ("Overview", "Executive Summary", "executive_summary.py"),
    ("Analysis", "Seasonality of profit", "question1.py"),
    ("Analysis", "Customer loyalty", "question2.py"),
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
