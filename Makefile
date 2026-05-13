# Convenience wrappers for the capstone stack. Every target is idempotent —
# running it twice does the same thing as running it once.

COMPOSE := docker compose
DBT_CMD := $(COMPOSE) run --rm --entrypoint dbt airflow-scheduler
DBT_DIRS := --project-dir /opt/airflow/dbt_project --profiles-dir /opt/airflow/dbt_project

# The Airflow container runs as uid 50000. The bind-mounted dbt_project/
# directory is host-owned, so dbt cannot write `package-lock.yml`,
# `dbt_packages/`, or other artifacts without help. Granting world-write
# on the project tree is the simplest portable fix — acceptable for a
# training environment running on a single laptop.
PERMISSIONS_FIX := chmod -R a+rwX dbt_project 2>/dev/null || true

.PHONY: up down build test reset logs shell-db shell-airflow dbt-deps \
        mlflow train-once register sweep promote forecast ml-test \
        reset-mlflow

up:
	@$(PERMISSIONS_FIX)
	$(COMPOSE) up -d
	@echo
	@. ./.env 2>/dev/null; \
		echo "Airflow UI:   http://localhost:$${AIRFLOW_HOST_PORT:-8080}"; \
		echo "Postgres:     localhost:$${POSTGRES_HOST_PORT:-5432} (see .env for creds)"

down:
	$(COMPOSE) down

# Full build: install dbt packages, load Bronze, then run dbt models.
build: dbt-deps
	$(COMPOSE) run --rm --entrypoint python airflow-scheduler /opt/airflow/ingest/load_bronze.py
	$(DBT_CMD) run $(DBT_DIRS)

test:
	$(DBT_CMD) test $(DBT_DIRS)

dbt-deps:
	$(DBT_CMD) deps $(DBT_DIRS)

# Wipe everything (including the Postgres volume) and rebuild from scratch.
reset:
	$(COMPOSE) down -v
	$(COMPOSE) up -d
	@echo "Waiting for Postgres to come up..."
	@until $(COMPOSE) exec -T postgres pg_isready -U $${POSTGRES_USER:-warehouse} >/dev/null 2>&1; do sleep 2; done
	$(MAKE) build

logs:
	$(COMPOSE) logs -f airflow-scheduler airflow-apiserver

shell-db:
	$(COMPOSE) exec postgres psql -U $${POSTGRES_USER:-warehouse} -d $${POSTGRES_DB:-warehouse}

shell-airflow:
	$(COMPOSE) exec airflow-scheduler bash

# ─────────────────────────────────────────────────────────────────────────
# Day 2 — ML lifecycle on the Gold layer
# ─────────────────────────────────────────────────────────────────────────

PYTHON_ML := $(COMPOSE) run --rm --entrypoint python --workdir /opt ml-runner
PYTEST_ML := $(COMPOSE) run --rm --entrypoint pytest --workdir /opt ml-runner

# Open the MLflow UI (informational — print the URL). On Codespaces the
# .devcontainer's postStartCommand writes MLFLOW_BASE_URL to .env with the
# forwarded `*.app.github.dev` URL; locally it falls back to localhost.
mlflow:
	@. ./.env 2>/dev/null; \
		echo "MLflow UI: $${MLFLOW_BASE_URL:-http://localhost:$${MLFLOW_HOST_PORT:-5000}}"

# Step 1 — track a single training run.
# Pass PARAMS=<key> to pick a non-default config from PARAMS_CHOICES in
# ml/train.py (canonical, small, deep, big). Bare `make train-once` runs
# the `canonical` preset.
train-once:
	$(PYTHON_ML) -m ml.train $(if $(PARAMS),--params $(PARAMS))

# Step 2 — train, register, and assign the @production alias.
register:
	$(PYTHON_ML) -m ml.train --register $(if $(PARAMS),--params $(PARAMS))

# Step 3 — sweep six configurations into separate runs.
sweep:
	$(PYTHON_ML) -m ml.sweep

# Step 4 — register the challenger if MAE beats the champion.
promote:
	$(PYTHON_ML) -m ml.promote

# Step 5 — load by alias and forecast one (plaza, direction, vehicle, month).
# Usage: make forecast PLAZA="..." DIR="..." VEH="..." MONTH="2020-01"
forecast:
	$(PYTHON_ML) -m ml.serve --plaza "$(PLAZA)" --direction "$(DIR)" --vehicle "$(VEH)" --month "$(MONTH)"

# Run the ml/ test suite (unit tests + integration smoke tests).
ml-test:
	$(PYTEST_ML) ml/tests -v

# Wipe MLflow state — runs, registered models, aliases, artifacts.
# Useful when re-running the Day 2 lab from scratch.
reset-mlflow:
	$(COMPOSE) down mlflow
	docker volume rm $$(basename "$$PWD" | tr '[:upper:]' '[:lower:]')_mlflow-data 2>/dev/null || true
	$(COMPOSE) up -d mlflow
	@echo "MLflow state reset."
