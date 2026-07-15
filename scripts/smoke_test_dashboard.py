"""Headless smoke test for the Streamlit dashboard.

Runs each page through Streamlit's AppTest runtime against the built DuckDB and
fails if any page raises. Each page runs in its OWN subprocess: Streamlit's
runtime keeps process-global state and running several AppTests in one
interpreter can crash the native duckdb/streamlit extensions, so isolation keeps
the check reliable (and lets one page's crash be reported without hiding others).

Requires the database to exist first (``python scripts/build_local_db.py`` +
``dbt build``).
"""
import subprocess
import sys
from pathlib import Path

DASHBOARD = Path(__file__).resolve().parent.parent / "dashboard"
PAGES = [
    "executive_summary.py",
    "question1.py",
    "question2.py",
    "customer_segments.py",
    "product_performance.py",
    "question3.py",
]

# Runs a single page in a fresh interpreter; exits non-zero on any exception.
_RUNNER = """
import sys
from pathlib import Path
page = sys.argv[1]
sys.path.insert(0, str(Path(page).resolve().parent))
from streamlit.testing.v1 import AppTest
app = AppTest.from_file(page, default_timeout=90).run()
if app.exception:
    for e in app.exception:
        print("  exception:", repr(e.value))
    sys.exit(1)
"""


def main() -> int:
    failures = []
    for page in PAGES:
        result = subprocess.run(
            [sys.executable, "-c", _RUNNER, str(DASHBOARD / page)]
        )
        if result.returncode == 0:
            print(f"OK   {page}")
        else:
            failures.append(page)
            print(f"FAIL {page} (exit {result.returncode})")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
