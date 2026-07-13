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


def _db_is_complete() -> bool:
    """True only if the warehouse exists *and* the final mart is present.

    Checking the final table (not just the file) matters: an interrupted build
    leaves a partial ``receipts.duckdb`` with only ``raw_receipts``, and treating
    that as "done" would serve an empty dashboard.
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


def _run(cmd: list[str], cwd: Path) -> None:
    """Run a build step, surfacing its output in the exception on failure."""
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        tail = (result.stdout or "")[-3000:] + "\n" + (result.stderr or "")[-2000:]
        raise RuntimeError(f"`{' '.join(cmd[-2:])}` failed (exit {result.returncode}):\n{tail}")


@st.cache_resource(show_spinner="Building the analytics database (first run only)…")
def _ensure_database() -> None:
    """Make sure a complete DuckDB warehouse is available before rendering.

    Resolution order:
      * Docker sets ``DUCKDB_FILE`` — the Airflow pipeline is the writer there.
      * A prebuilt ``receipts.duckdb`` is committed to the repo, so read-only
        hosts like Streamlit Community Cloud (whose sandbox filesystem can't be
        written) serve it directly with no build.
      * Otherwise (local dev with the DB deleted) rebuild it from the committed
        raw JSON with the same two steps Airflow orchestrates.
    """
    if os.getenv("DUCKDB_FILE"):
        return  # externally managed (Docker warehouse / Airflow)
    if _db_is_complete():
        return  # committed prebuilt DB (Cloud), or already built locally

    # Drop any partial DB left by an interrupted earlier attempt, then rebuild.
    Path(DUCKDB_FILE).unlink(missing_ok=True)
    # 1. Land the raw JSON into main.raw_receipts (absolute output path).
    _run([sys.executable, str(ROOT / "scripts" / "build_local_db.py")], cwd=ROOT)
    # 2. Build the dbt models. The dev profile's output path is relative
    #    (`receipts.duckdb`), so dbt must run from the project dir — exactly as
    #    the documented `cd dbt/receipts_analytics && dbt ...` workflow — or it
    #    would open a different, empty database.
    dbt_exe = Path(sys.executable).parent / "dbt"
    dbt = str(dbt_exe) if dbt_exe.exists() else "dbt"
    _run([dbt, "deps"], cwd=DBT_PROJECT)
    _run([dbt, "run", "--target", "dev", "--profiles-dir", "."], cwd=DBT_PROJECT)

    if not _db_is_complete():
        raise RuntimeError("Build finished but fct_business_kpis is still missing.")


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
