# Airflow image with dbt-postgres baked in. Building locally keeps the
# Compose file pinned to a known-good combination and avoids per-container
# pip installs at runtime.
FROM apache/airflow:3.2.1-python3.11

# dbt-postgres pulls dbt-core as a transitive dependency. sqlalchemy and
# psycopg2-binary are already shipped with Airflow, but pandas is not.
#
# The dbt-core / dbt-common / mashumaro trio must be pinned explicitly:
# dbt-postgres==1.8.2 alone does not constrain them, and newer mashumaro
# releases (3.15+) trigger an MRO crash inside dbt.contracts.graph.manifest
# (`Cannot create a consistent method resolution order`). The versions
# below are the ones the Day 2 dry-run validated end-to-end.
USER airflow
RUN pip install --no-cache-dir \
    "dbt-postgres==1.8.2" \
    "dbt-core==1.10.8" \
    "dbt-adapters==1.16.3" \
    "dbt-common==1.27.1" \
    "mashumaro[msgpack]==3.14" \
    "pandas==2.2.3"
