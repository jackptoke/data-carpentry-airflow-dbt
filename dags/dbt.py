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
from cosmos.constants import TestBehavior

from receipts import raw_receipts

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt" / "receipts_analytics"
# dbt lives in the project virtualenv mounted at /opt/airflow/.venv
DBT_EXECUTABLE = PROJECT_ROOT / ".venv" / "bin" / "dbt"

profile_config = ProfileConfig(
    profile_name="receipts_analytics",
    target_name="prod",
    profiles_yml_filepath=DBT_PROJECT_DIR / "profiles.yml",
)

execution_config = ExecutionConfig(dbt_executable_path=str(DBT_EXECUTABLE))

# Render one task per model, immediately followed by that model's tests, and
# install dbt packages (dbt_utils) during rendering.
render_config = RenderConfig(
    test_behavior=TestBehavior.AFTER_EACH,
    dbt_deps=True,
)

default_args = {
    "owner": "jack",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dbt_receipts_analytics = DbtDag(
    dag_id="dbt_receipts_analytics",
    project_config=ProjectConfig(dbt_project_path=DBT_PROJECT_DIR),
    profile_config=profile_config,
    execution_config=execution_config,
    render_config=render_config,
    # Asset-scheduled: run after the raw_receipts ingestion asset is produced.
    schedule=[raw_receipts],
    default_args=default_args,
    tags=["dbt", "receipts"],
    doc_md=__doc__,
)
