# Pinned for reproducible builds (Airflow 3 SDK is used by the DAGs).
FROM apache/airflow:3.0.6
WORKDIR /opt/airflow/

# Install Python deps first (dbt-duckdb + Cosmos) for better layer caching.
# dbt is installed into the image here; there is no separate venv to copy.
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY config/airflow.cfg config/airflow.cfg
COPY dags/ dags/
# --chown so the airflow user can write dbt_packages/, target/ and logs/.
COPY --chown=airflow:0 dbt/ dbt/

# Install dbt packages and pre-compile the manifest so Cosmos can render the
# DAG from the manifest at parse time (fast, no dbt shell-out on every parse).
RUN cd /opt/airflow/dbt/receipts_analytics \
    && dbt deps \
    && dbt parse --profiles-dir . --target prod
