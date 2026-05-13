# Airflow image with dbt-postgres baked in. Building locally keeps the
# Compose file pinned to a known-good combination and avoids per-container
# pip installs at runtime.
FROM apache/airflow:3.2.1-python3.11

# dbt-postgres pulls dbt-core as a transitive dependency. sqlalchemy and
# psycopg2-binary are already shipped with Airflow, but pandas is not.
USER airflow
RUN pip install --no-cache-dir \
    "dbt-postgres==1.8.2" \
    "pandas==2.2.3"
