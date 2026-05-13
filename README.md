# Capstone Starter — Toll-Traffic Pipeline

A self-contained Docker stack for the 3-hour data engineering capstone. It
ships a Postgres warehouse, Airflow 3, and dbt — plus a pre-built Bronze
loader and a worked staging example — so trainees can spend their time on
the actual exercise (Silver, Gold, tests, contract) instead of on plumbing.

## Prerequisites

- Docker Engine 24+ with Docker Compose v2
- ~10 GB of free disk
- A POSIX shell. On macOS and Linux this is the default. On Windows,
  open the project from a **WSL2 shell** (Docker Desktop on Windows
  already runs on WSL2). The Makefile is bash-flavored and will not run
  from PowerShell or cmd. PowerShell users can still drive the stack
  with raw `docker compose` commands — see *Without make* below.
- (Optional) `make`. Every Make target is a thin wrapper around
  `docker compose` — `Without make` shows the underlying commands.

## Quickstart

```bash
git clone <this-repo>
cd antt-template
cp .env.example .env

make up                    # bring the stack up
# wait ~30s for Postgres + Airflow to settle

make build                 # load Bronze and run dbt
make test                  # run dbt tests

# Airflow UI:    http://localhost:8080  (admin / admin by default)
# Postgres:      localhost:5432         (see .env for creds)
```

When you are done:

```bash
make down       # stop the stack, keep the data
make reset      # nuke the volume and rebuild from scratch
```

## Without make

If `make` is not available (typical on PowerShell/cmd, or any environment
without GNU Make), every Make target maps to a one-line `docker compose`
call. Run them directly:

```powershell
# bring the stack up
docker compose up -d

# load Bronze
docker compose run --rm --entrypoint python airflow-scheduler `
  /opt/airflow/ingest/load_bronze.py

# install dbt packages, then run + test
docker compose run --rm --entrypoint dbt airflow-scheduler `
  deps --project-dir /opt/airflow/dbt_project `
       --profiles-dir /opt/airflow/dbt_project
docker compose run --rm --entrypoint dbt airflow-scheduler `
  run  --project-dir /opt/airflow/dbt_project `
       --profiles-dir /opt/airflow/dbt_project
docker compose run --rm --entrypoint dbt airflow-scheduler `
  test --project-dir /opt/airflow/dbt_project `
       --profiles-dir /opt/airflow/dbt_project

# psql into the warehouse
docker compose exec postgres psql -U warehouse -d warehouse

# stop the stack (keep data)
docker compose down

# wipe everything (drop the volume too)
docker compose down -v
```

The PowerShell line continuation is the backtick (`` ` ``); on bash use
backslash (`\`). The above is otherwise identical to what the Makefile
runs internally.

> **Windows note**: when running on PowerShell/cmd, the `make up`
> permissions-fix step (chmod) does not run. If you hit "permission
> denied" errors on `package-lock.yml` later, switch to a WSL2 shell.

## Optional: running dbt locally with uv

The Docker stack is the supported path. Participants who would rather run
dbt directly on their host (faster iteration on SQL, IDE integration) can
do so with `uv` — this is purely optional and not required at any point
during the capstone.

```bash
# one-time setup
uv venv && source .venv/bin/activate
uv pip install dbt-postgres==1.8.2

# point dbt at the warehouse running in Docker
export POSTGRES_HOST=localhost POSTGRES_PORT=5432 \
       POSTGRES_DB=warehouse POSTGRES_USER=warehouse \
       POSTGRES_PASSWORD=warehouse
cd dbt_project
dbt deps
dbt run
dbt test
```

Make sure `make up` is running so the warehouse is reachable on
`localhost:5432`.

## What's already built

- **Bronze loader** (`ingest/load_bronze.py`) — reads the raw CSV with the
  correct delimiter and Latin-1 encoding, writes
  `bronze.toll_traffic_raw`, adds a `_loaded_at` audit column.
- **Staging example** (`dbt_project/models/staging/stg_toll_traffic.sql`) —
  a complete worked example: source ref, trims, cast, plus four dbt tests
  in `_staging.yml`. Copy this pattern.
- **Airflow DAG skeleton** (`airflow/dags/capstone_etl_dag.py`) — the
  `load_bronze` task is wired and runs end-to-end. The `dbt_run` and
  `dbt_test` tasks are stubbed with `TODO` markers for you to complete.
- **CI workflow** (`.github/workflows/ci.yml`) — runs `dbt parse` on every
  pull request to catch broken refs, sources, and Jinja before merge.
- **Gold contract template** (`docs/gold-contract-template.md`) — the
  document you will fill in for the Block 5 handoff.

## What you build

- Silver models in `dbt_project/models/silver/` (start by copying
  `stg_toll_traffic.sql`).
- Gold models in `dbt_project/models/gold/` — at least one fact + one
  dimension.
- dbt tests on every model you add (`not_null`, `unique`, `accepted_values`,
  custom expressions). The CI build will lint your SQL.
- Wire up the `dbt_run` and `dbt_test` tasks inside the DAG and connect the
  dependencies (`load_bronze >> dbt_run >> dbt_test`).
- Fill in `docs/gold-contract-template.md` and commit it alongside your
  Gold release.

## Repo layout

```
antt-template/
├── data/raw/all.csv           Source dataset (already in place)
├── ingest/                    Bronze loader (Python)
├── dbt_project/               dbt project (staging done; silver/gold empty)
├── airflow/                   DAGs + custom Airflow image with dbt
├── postgres-init/             Schema bootstrap for Postgres
├── docs/                      Gold contract template
└── .github/workflows/ci.yml   PR linting
```

## Troubleshooting

- **Airflow login fails.** First-run user creation is handled by the
  `airflow-init` service; if you started the stack before copying `.env`
  it may have skipped. Run `make reset`.
- **`make build` complains about dbt packages.** Run `make dbt-deps` once.
  It is also baked into `make build`, but standalone `dbt run` calls need
  it.
- **Mojibake in Bronze (`Aço` shows up as `A�o`).** The loader is fixed;
  if you rolled your own and see this, the encoding is wrong — must be
  `latin-1`, not `utf-8`.

---

For the full capstone briefing, see the Day 1 capstone docs in the
companion training repo (`brisa-enterprise-grade-data-training`, Session
"Capstone Day 1").
