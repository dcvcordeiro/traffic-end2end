"""Capstone ETL DAG.

Pipeline:

    load_bronze  ->  dbt_run  ->  dbt_test  ->  quality_gate
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
    description="Bronze load + dbt build + quality gate.",
    schedule="@monthly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    # Serialise runs: the Bronze loader rebuilds `bronze.toll_traffic_raw`
    # in place. Concurrent runs would race and crash on a unique-constraint
    # violation while pandas creates the table.
    max_active_runs=1,
    tags=["capstone", "bronze", "dbt"],
)
def capstone_etl():

    @task(task_id="load_bronze")
    def load_bronze_task() -> int:
        """Load the raw CSV into `bronze.toll_traffic_raw`."""
        from load_bronze import _build_conn_str, load_bronze, DEFAULT_CSV_PATH

        csv_path = str(Path(DEFAULT_CSV_PATH))
        rows = load_bronze(csv_path, _build_conn_str())
        print(f"Bronze load complete: {rows:,} rows")
        return rows

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            "dbt run "
            "--project-dir /opt/airflow/dbt_project "
            "--profiles-dir /opt/airflow/dbt_project"
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            "dbt test "
            "--project-dir /opt/airflow/dbt_project "
            "--profiles-dir /opt/airflow/dbt_project"
        ),
    )

    @task(task_id="quality_gate")
    def quality_gate() -> int:
        """Fail if `gold.fact_traffic_monthly` looks empty or stale."""
        import os
        import psycopg2

        conn = psycopg2.connect(
            host=os.environ["POSTGRES_HOST"],
            port=os.environ["POSTGRES_PORT"],
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
        )
        with conn, conn.cursor() as cur:
            cur.execute("select count(*) from gold.fact_traffic_monthly")
            (row_count,) = cur.fetchone()

        # Threshold sized at ~70% of the expected ~60K rows for the
        # recommended grain. Adjust if you pick a different grain.
        if row_count < 40_000:
            raise ValueError(
                f"Gold fact_traffic_monthly has only {row_count:,} rows - "
                "expected >= 40,000."
            )
        print(f"Quality gate OK: {row_count:,} rows in fact_traffic_monthly")
        return row_count

    bronze = load_bronze_task()
    bronze >> dbt_run >> dbt_test >> quality_gate()


capstone_etl()
