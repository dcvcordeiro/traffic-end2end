# Model Card — Forecast Traffic Volume

> Copy this file to `docs/model-card.md`, fill in every section, and commit.
> This document is the contract Day 3 reads first.

## Overview

One paragraph: what this model predicts, who consumes it, and how often
it should be retrained.

*Example:* "Predicts monthly toll-traffic volume per (plaza, direction,
vehicle type) one month ahead. Consumed by the Day 3 Power BI report
("Forecast vs Actual"). Retraining cadence: monthly, after the ANTT
publishes the new month's actuals."

## Data

| Field             | Value                                         |
|-------------------|-----------------------------------------------|
| Source            | `gold.fact_traffic_monthly` + dimensions      |
| Training window   | `<YYYY-MM>` to `<YYYY-MM>`                    |
| Holdout window    | last 6 months of the training window          |
| Training rows     | `<integer>`                                   |
| Holdout rows      | `<integer>`                                   |

## Features

| Column         | Type   | Why it is used                                 |
|----------------|--------|------------------------------------------------|
| `plaza_id`     | int    | Identifies the plaza — encoded from plaza_name |
| `vehicle_id`   | int    | Identifies the vehicle type                    |
| `direction_id` | int    | Identifies the direction                       |
| `year`         | int    | Captures multi-year trend                      |
| `month`        | int    | Captures seasonality                           |
| `lag_1`        | float  | Volume at this key one month ago               |
| `lag_12`       | float  | Volume at this key one year ago (seasonality)  |

*Anything explicitly excluded:* `concessionaria` (high-cardinality, not
required by the forecast question), `direction` as a string (replaced
by `direction_id`).

## Performance

| Metric                                       | Value             |
|----------------------------------------------|-------------------|
| MAE on holdout (vehicles/month)              | `<float>`         |
| RMSE on holdout (vehicles/month)             | `<float>`         |
| Mean of `volume_total` on holdout            | `<float>`         |
| Promotion comparison (from `make promote`)   | `Challenger wins. v<N>` *or* `Champion holds.` |

## Registry

| Field                  | Value                                            |
|------------------------|--------------------------------------------------|
| Registered model name  | `ForecastTrafficVolume`                          |
| Current `@production`  | `v<N>`                                           |
| URI Day 3 will load    | `models:/ForecastTrafficVolume@production`       |

## Caveats and Owner

- Plaza/month combinations with under 12 months of history were dropped
  in the lag-feature step. Predictions for newly-opened plazas are not
  supported until they have one year of data.
- The `month` and `year` features assume the dataset's calendar (Jan 2010
  – Dec 2019). Predicting outside that range requires inputs whose
  `lag_1` and `lag_12` are computable.
- The `random_state=42` makes the run reproducible; if the Gold layer
  changes, retrain.

**Owner.** `<First Last>` — `<contact handle: Slack/email>`

## Sign-off

Signed by `<First Last>` on `<YYYY-MM-DD>`.
