"""Headless smoke test for the Streamlit dashboard.

Runs each page through Streamlit's AppTest runtime against the built DuckDB and
exits non-zero if any page raises. Requires the database to exist first
(``python scripts/build_local_db.py`` + ``dbt build``).
"""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

DASHBOARD = Path(__file__).resolve().parent.parent / "dashboard"
sys.path.insert(0, str(DASHBOARD))

PAGES = ["question1.py", "question2.py", "question3.py"]


def main() -> int:
    failures = []
    for page in PAGES:
        app = AppTest.from_file(str(DASHBOARD / page), default_timeout=90).run()
        if app.exception:
            messages = [repr(e.value) for e in app.exception]
            failures.append(page)
            print(f"FAIL {page}: {messages}")
        else:
            print(f"OK   {page}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
