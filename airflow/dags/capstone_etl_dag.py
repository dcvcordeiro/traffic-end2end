"""Capstone ETL DAG.

Pipeline:

    load_bronze  ->  dbt_run  ->  dbt_test

Only `load_bronze` is wired up. The dbt tasks are stubbed with TODO markers
so trainees can implement them as part of the exercise.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from airflow.sdk import dag, task
from airflow.providers.standard.operators.bash import BashOperator

# The ingest module lives at /opt/airflow/ingest inside the container; make
# sure it is importable regardless of how Airflow launches the worker.
INGEST_DIR = "/opt/airflow/ingest"
if INGEST_DIR not in sys.path:
    sys.path.insert(0, INGEST_DIR)


@dag(
    dag_id="capstone_etl",
    description="Bronze load + dbt build for the toll-traffic capstone.",
    schedule="@monthly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    # Serialise runs: the Bronze loader rebuilds `bronze.toll_traffic_raw`
    # in place, so two concurrent runs would race and one would crash with
    # a unique-constraint violation. ETLs that rebuild a table should not
    # run in parallel against the same warehouse.
    max_active_runs=1,
    tags=["capstone", "bronze", "dbt"],
)
def capstone_etl():

    @task(task_id="load_bronze")
    def load_bronze_task() -> int:
        """Load the raw CSV into `bronze.toll_traffic_raw`."""
        # Imported lazily so DAG parsing does not require pandas/sqlalchemy.
        from load_bronze import _build_conn_str, load_bronze, DEFAULT_CSV_PATH

        csv_path = str(Path(DEFAULT_CSV_PATH))
        rows = load_bronze(csv_path, _build_conn_str())
        print(f"Bronze load complete: {rows:,} rows")
        return rows

    # ------------------------------------------------------------------
    # TODO (trainee): implement the `dbt_run` task.
    # Hint: use BashOperator to execute
    #   `dbt run --project-dir /opt/airflow/dbt_project --profiles-dir /opt/airflow/dbt_project`
    # ------------------------------------------------------------------
    # dbt_run = BashOperator(
    #     task_id="dbt_run",
    #     bash_command=(
    #         "dbt run "
    #         "--project-dir /opt/airflow/dbt_project "
    #         "--profiles-dir /opt/airflow/dbt_project"
    #     ),
    # )

    # ------------------------------------------------------------------
    # TODO (trainee): implement the `dbt_test` task.
    # Same pattern as `dbt_run`, but with `dbt test`.
    # ------------------------------------------------------------------
    # dbt_test = BashOperator(
    #     task_id="dbt_test",
    #     bash_command=(
    #         "dbt test "
    #         "--project-dir /opt/airflow/dbt_project "
    #         "--profiles-dir /opt/airflow/dbt_project"
    #     ),
    # )

    bronze = load_bronze_task()

    # ------------------------------------------------------------------
    # TODO (trainee): wire dependencies once the dbt tasks above are real.
    #     bronze >> dbt_run >> dbt_test
    # ------------------------------------------------------------------
    _ = bronze


capstone_etl()
