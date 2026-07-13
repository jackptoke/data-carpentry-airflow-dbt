# Pinned for reproducible builds (Airflow 3 SDK is used by the DAGs).
# Must match the apache-airflow version resolved in requirements.txt (3.3.0) so
# airflow-core and the base image agree. A mismatch half-upgrades core while
# leaving the base image's providers behind, crashing the api-server.
# The -python3.12 suffix is required: the default 3.3.0 tag ships Python 3.13,
# for which the lockfile's numpy==1.26.4 has no wheel (it would build from source
# and fail). requirements.txt is locked against Python 3.12.
FROM apache/airflow:3.3.0-python3.12
WORKDIR /opt/airflow/

# Keep this in sync with the base image tag / requirements.txt airflow version.
ARG AIRFLOW_VERSION=3.3.0

# Install Python deps first (dbt-duckdb + Cosmos) for better layer caching.
# dbt is installed into the image here; there is no separate venv to copy.
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Airflow 3.3 unbundled the FAB auth manager into a separate provider, and the
# lockfile doesn't include it — but docker-compose sets AUTH_MANAGER=FabAuthManager.
# Install it via the official constraints so flask-appbuilder resolves to the
# Flask 3.x-compatible line (5.2.1) matching the Flask 3.1.3 already pinned above.
RUN pip install --no-cache-dir "apache-airflow-providers-fab==3.7.1" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.12.txt"

COPY config/airflow.cfg config/airflow.cfg
COPY dags/ dags/
# --chown so the airflow user can write dbt_packages/, target/ and logs/.
COPY --chown=airflow:0 dbt/ dbt/

# Install dbt packages and pre-compile the manifest so Cosmos can render the
# DAG from the manifest at parse time (fast, no dbt shell-out on every parse).
RUN cd /opt/airflow/dbt/receipts_analytics \
    && dbt deps \
    && dbt parse --profiles-dir . --target prod
