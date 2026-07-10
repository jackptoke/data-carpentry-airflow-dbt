# Pinned for reproducible builds (Airflow 3 SDK is used by the DAGs).
FROM apache/airflow:3.0.6
WORKDIR /opt/airflow/
COPY requirements.txt requirements.txt
COPY dbt/ dbt/
COPY config/airflow.cfg config/airflow.cfg
COPY .venv/ .venv/
COPY dags/ dags/
RUN pip install --no-cache-dir -r requirements.txt