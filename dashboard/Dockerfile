# Standalone dashboard image for a persistent container host (Railway).
#
# Self-contained: the prebuilt DuckDB warehouse is baked in, so there is no
# runtime build, no Airflow, and no shared volume. Build context is the repo
# root (see railway.json / docker build -f dashboard/Dockerfile .).
FROM python:3.12-slim

WORKDIR /app

# ABI-coherent, pinned deps (numpy 2.0–2.4 / duckdb 1.3.1 / pyarrow 25 — see
# dashboard/requirements.txt). Installed first for layer caching.
COPY dashboard/requirements.txt dashboard/requirements.txt
RUN pip install --no-cache-dir -r dashboard/requirements.txt

# The dashboard app and the committed, read-only warehouse it serves. Paths
# mirror the repo layout so constants.py resolves the DB at ../dbt/... .
COPY dashboard/ dashboard/
COPY dbt/receipts_analytics/receipts.duckdb dbt/receipts_analytics/receipts.duckdb

# Railway injects $PORT at runtime; Streamlit binds to it on all interfaces.
EXPOSE 8505
CMD ["sh", "-c", "streamlit run dashboard/streamlit_app.py --server.port=${PORT:-8505} --server.address=0.0.0.0 --server.headless=true"]
