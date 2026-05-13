"""Load the raw toll-traffic CSV into the Bronze layer of the warehouse.

The source file is shipped with quirks the loader must absorb so every
downstream layer can rely on clean Postgres semantics:

- Delimiter is ``;`` (not ``,``).
- Encoding is ISO-8859-1 / Latin-1. Reading as UTF-8 mangles ``ç``/``ã``.
- Column names use mixed casing; we lowercase them on the way in to follow
  Postgres conventions.

The table is rewritten in full on every run (``if_exists='replace'``). That is
fine for a training environment; production would append + dedup on a natural
key.
"""

from __future__ import annotations

import argparse
import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text

DEFAULT_CSV_PATH = "/data/raw/all.csv"
BRONZE_SCHEMA = "bronze"
BRONZE_TABLE = "toll_traffic_raw"


def _build_conn_str() -> str:
    """Assemble a SQLAlchemy connection string from environment variables."""
    host = os.environ["POSTGRES_HOST"]
    port = os.environ.get("POSTGRES_PORT", "5432")
    db = os.environ["POSTGRES_DB"]
    user = os.environ["POSTGRES_USER"]
    password = os.environ["POSTGRES_PASSWORD"]
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def load_bronze(csv_path: str, conn_str: str) -> int:
    """Load ``csv_path`` into ``bronze.toll_traffic_raw``.

    Returns the number of rows written.
    """
    # Latin-1 is mandatory: the source file uses cedilhas and tildes that are
    # invalid UTF-8 byte sequences. Pandas will raise on UTF-8 decode.
    df = pd.read_csv(csv_path, sep=";", encoding="latin-1")

    # Lowercase column names so dbt + SQL stay idiomatic on Postgres.
    df.columns = [c.lower() for c in df.columns]

    engine = create_engine(conn_str)
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {BRONZE_SCHEMA}"))
        # Drop with CASCADE so we sweep along any dependent dbt views
        # (notably staging.stg_toll_traffic). Pandas' if_exists='replace'
        # issues a plain DROP that fails once a downstream model exists.
        # dbt rebuilds its views on the next run.
        conn.execute(
            text(f"DROP TABLE IF EXISTS {BRONZE_SCHEMA}.{BRONZE_TABLE} CASCADE")
        )

    df.to_sql(
        BRONZE_TABLE,
        engine,
        schema=BRONZE_SCHEMA,
        if_exists="append",
        index=False,
        chunksize=10_000,
        method="multi",
    )

    # Add the audit column post-load. Doing it via ALTER keeps the pandas
    # to_sql call schemaless and avoids dtype-mapping surprises.
    with engine.begin() as conn:
        conn.execute(
            text(
                f"ALTER TABLE {BRONZE_SCHEMA}.{BRONZE_TABLE} "
                f"ADD COLUMN IF NOT EXISTS _loaded_at TIMESTAMP DEFAULT NOW()"
            )
        )
        conn.execute(
            text(
                f"UPDATE {BRONZE_SCHEMA}.{BRONZE_TABLE} "
                f"SET _loaded_at = NOW() WHERE _loaded_at IS NULL"
            )
        )

    return len(df)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv-path",
        default=os.environ.get("BRONZE_CSV_PATH", DEFAULT_CSV_PATH),
        help="Path to the source CSV (defaults to /data/raw/all.csv).",
    )
    args = parser.parse_args()

    conn_str = _build_conn_str()
    rows = load_bronze(args.csv_path, conn_str)
    print(f"Loaded {rows:,} rows into {BRONZE_SCHEMA}.{BRONZE_TABLE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
