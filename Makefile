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

.PHONY: up down build test reset logs shell-db shell-airflow dbt-deps

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
