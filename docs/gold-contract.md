# Gold Layer Data Contract

This contract describes the Gold layer produced by the `capstone_etl` DAG.
It is the only artifact Day 2 should need to know about — the SQL behind
each table is in `dbt_project/models/gold/`, but every property a consumer
relies on is documented here.

## Overview

The Gold layer is a star schema over Brazilian highway toll-plaza traffic
volumes published by ANTT, covering April 2010 through September 2019.
One fact table holds monthly volume counts; three dimensions describe
the plaza, vehicle type, and month. It is consumed by the Day 2 forecast
model and the Day 3 Power BI report. Refreshed monthly by the
`capstone_etl` Airflow DAG; in the training environment it is rebuilt on
demand via `make build`.

---

## Tables

### `gold.fact_traffic_monthly`

- **Grain:** one row per *(plaza, direction, vehicle type, month)*.
- **Primary key:** `(date_key, plaza_key, vehicle_key, direction)`.
- **Refresh cadence:** monthly, triggered by the `capstone_etl` DAG
  (`@monthly`, `max_active_runs=1`).
- **Owner:** the capstone team.
- **Row count (current):** ~59,700 rows.

#### Columns

| Column | Type | Description |
| ------ | ---- | ----------- |
| `date_key` | text | Surrogate FK to `dim_date.date_key` (md5 of `month_start`). |
| `plaza_key` | text | Surrogate FK to `dim_plaza.plaza_key` (md5 of `plaza_name`). |
| `vehicle_key` | text | Surrogate FK to `dim_vehicle.vehicle_key` (md5 of `vehicle_type`). |
| `direction` | text | Direction of travel — degenerate dim. One of `Norte`, `Sul`, `Leste`, `Oeste`, `Sentido 1`, `Sentico 2`. |
| `volume_total` | int | Monthly total vehicles passing the plaza in that direction, for that vehicle type. Always ≥ 0. |

#### Tests

- `not_null` and `relationships` on all three FKs (`date_key`, `plaza_key`, `vehicle_key`).
- `accepted_values` on `direction` (the six allowed values).
- `not_null` on `volume_total`; `expression_is_true` for `>= 0`.

#### Known caveats

- **3 negative-volume rows** in source were dropped at the Silver layer.
  Total row count is therefore 3 fewer than a naive aggregation would
  produce.
- **Direction is not harmonized.** Some concessionaires publish cardinal
  directions, others use generic `Sentido 1/2`. There is no per-plaza
  mapping; consumers comparing "north vs. south" across plazas should
  filter to the cardinal-direction set.
- **Irregular plaza coverage.** Not every plaza has data for all 120
  months — concessions started at different dates over the decade.
  Consumers doing time-series forecasts should establish per-plaza
  history length before training.
- **Categoria axis dropped.** The 46 `Categoria` values in the source
  collapse to the cleaner 3-value `vehicle_type` axis. Analyses that
  need fare-category granularity will not be served by this Gold layer.

---

### `gold.dim_date`

- **Grain:** one row per month.
- **Primary key:** `date_key`.
- **Row count:** 120 (April 2010 through September 2019).

#### Columns

| Column | Type | Description |
| ------ | ---- | ----------- |
| `date_key` | text | Surrogate (md5 of `month_start`). |
| `month_start` | date | First day of the month. |
| `year` | int | 4-digit year. |
| `quarter` | int | 1–4. |
| `month` | int | 1–12. |
| `year_month` | text | `YYYY-MM` formatted string for grouping/filtering. |

#### Tests

- `not_null` and `unique` on `date_key` and `month_start`.

---

### `gold.dim_plaza`

- **Grain:** one row per plaza.
- **Primary key:** `plaza_key`.
- **Row count:** 128.

#### Columns

| Column | Type | Description |
| ------ | ---- | ----------- |
| `plaza_key` | text | Surrogate (md5 of `plaza_name`). |
| `plaza_name` | text | Plaza identifier as published by ANTT, e.g. `Praça 01  BR-393/RJ km 125,00`. Free-form string. |
| `concessionaria` | text | Concessionaire operating the plaza. Stable across the dataset — every plaza has exactly one. |

#### Tests

- `not_null` and `unique` on `plaza_key` and `plaza_name`.

#### Known caveats

- `plaza_name` strings embed highway, state, and km marker as free text.
  Consumers needing those fields parsed should do so downstream — the
  Gold layer keeps the raw label.

---

### `gold.dim_vehicle`

- **Grain:** one row per vehicle type.
- **Primary key:** `vehicle_key`.
- **Row count:** 3.

#### Columns

| Column | Type | Description |
| ------ | ---- | ----------- |
| `vehicle_key` | text | Surrogate (md5 of `vehicle_type`). |
| `vehicle_type` | text | One of `Comercial`, `Moto`, `Passeio`. |

#### Tests

- `not_null`, `unique`, `accepted_values` on `vehicle_type`.

---

## Versioning policy

- **Additive changes** (new columns, new rows): no notice required.
- **Breaking changes** (removing or renaming columns, changing types or
  grain): announce at least one sprint in advance, ship behind a `_v2`
  table, and deprecate the old one with a fixed sunset date.

A change to the grain of `fact_traffic_monthly` is by definition a
breaking change.

---

## Sign-off

The team accepts this contract as the basis for Day 2:

- Name: ____________________
- Date: ____________________
