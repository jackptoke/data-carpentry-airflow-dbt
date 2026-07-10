"""Transformation layer: run the dbt project as native Airflow tasks via Cosmos.

astronomer-cosmos renders the ``receipts_analytics`` dbt project into a task
group with one task per model plus its tests, so lineage, retries and test
failures are all visible in the Airflow UI (instead of a single opaque
``dbt run`` BashOperator).

The DAG is asset-scheduled: it runs whenever the ``raw_receipts`` ingestion
asset (see dags/receipts.py) is refreshed.
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from cosmos import (
    DbtDag,
    ExecutionConfig,
    ProfileConfig,
    ProjectConfig,
    RenderConfig,
)
from cosmos.constants import LoadMode, TestBehavior
from airflow.sdk import Asset

# The ingestion asset produced by dags/receipts.py. Referenced by identity (not
# imported) so importing this DAG file does not re-register the raw_receipts DAG.
RAW_RECEIPTS_ASSET = Asset(name="raw_receipts", uri="duckdb://main/raw_receipts")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt" / "receipts_analytics"
# dbt is installed into the Airflow image (via requirements.txt) and is on PATH.
DBT_EXECUTABLE = "/home/airflow/.local/bin/dbt"
# Pre-compiled at image build time (see Dockerfile) so the DAG renders from the
# manifest instead of shelling out to dbt on every parse.
MANIFEST_PATH = DBT_PROJECT_DIR / "target" / "manifest.json"

profile_config = ProfileConfig(
    profile_name="receipts_analytics",
    target_name="prod",
    profiles_yml_filepath=DBT_PROJECT_DIR / "profiles.yml",
)

execution_config = ExecutionConfig(dbt_executable_path=DBT_EXECUTABLE)

# Render one task per model, immediately followed by that model's tests, from
# the pre-built manifest (fast, deterministic, no dbt run at parse time).
render_config = RenderConfig(
    test_behavior=TestBehavior.AFTER_EACH,
    load_method=LoadMode.DBT_MANIFEST,
    dbt_executable_path=DBT_EXECUTABLE,
)

default_args = {
    "owner": "jack",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

dbt_receipts_analytics = DbtDag(
    dag_id="dbt_receipts_analytics",
    project_config=ProjectConfig(
        dbt_project_path=DBT_PROJECT_DIR,
        manifest_path=MANIFEST_PATH,
    ),
    profile_config=profile_config,
    execution_config=execution_config,
    render_config=render_config,
    # Asset-scheduled: run after the raw_receipts ingestion asset is produced.
    schedule=[RAW_RECEIPTS_ASSET],
    default_args=default_args,
    # DuckDB is single-writer: run one model/test task at a time so concurrent
    # dbt processes don't collide on the database file's write lock.
    max_active_tasks=1,
    max_active_runs=1,
    tags=["dbt", "receipts"],
    doc_md=__doc__,
)
