"""Step 5 serving: load the current @production model and predict.

Resolves user-readable plaza/direction/vehicle/month inputs into the
encoded feature row the model expects, then loads the model by alias
from the registry and prints a single forecast.

You finish this file by writing the load-by-alias call.

Usage:
    make forecast PLAZA="Praça 01  BR-393/RJ km 125,00" \\
                  DIR="Norte" \\
                  VEH="Passeio" \\
                  MONTH="2020-01"
"""
from __future__ import annotations

import argparse
import sys

import mlflow
import mlflow.pyfunc
import pandas as pd

from ml.features import FEATURE_COLS, build_engine

REGISTERED_MODEL_NAME = "ForecastTrafficVolume"
PRODUCTION_ALIAS = "production"
MODEL_URI = f"models:/{REGISTERED_MODEL_NAME}@{PRODUCTION_ALIAS}"


def _load_history(engine):
    return pd.read_sql(
        """
        select d.month_start, p.plaza_name, v.vehicle_type,
               f.direction, f.volume_total
        from gold.fact_traffic_monthly as f
        join gold.dim_date    as d on d.date_key    = f.date_key
        join gold.dim_plaza   as p on p.plaza_key   = f.plaza_key
        join gold.dim_vehicle as v on v.vehicle_key = f.vehicle_key
        """,
        engine,
        parse_dates=["month_start"],
    )


def _cat_id(series: pd.Series, value: str, label: str) -> int:
    """Return the cat-code of `value` in `series`, matching features.py."""
    categories = series.astype("category").cat.categories
    if value not in categories:
        raise SystemExit(
            f"{label} not found: {value!r}\n"
            f"available: {list(categories)[:5]} ... ({len(categories)} total)"
        )
    return int(list(categories).index(value))


def _build_row(plaza: str, direction: str, vehicle: str, month: str) -> pd.DataFrame:
    engine = build_engine()
    hist = _load_history(engine)

    plaza_id     = _cat_id(hist["plaza_name"],   plaza,     "plaza")
    vehicle_id   = _cat_id(hist["vehicle_type"], vehicle,   "vehicle")
    direction_id = _cat_id(hist["direction"],    direction, "direction")

    target = pd.to_datetime(f"{month}-01")
    series = hist[
        (hist["plaza_name"]   == plaza)
        & (hist["direction"]   == direction)
        & (hist["vehicle_type"] == vehicle)
    ]

    def _vol_at(d):
        match = series[series["month_start"] == d]
        if match.empty:
            raise SystemExit(
                f"no historical volume for "
                f"{plaza!r}/{direction!r}/{vehicle!r} at {d:%Y-%m}"
            )
        return float(match["volume_total"].iloc[0])

    row = pd.DataFrame([{
        "plaza_id":     plaza_id,
        "vehicle_id":   vehicle_id,
        "direction_id": direction_id,
        "year":  int(target.year),
        "month": int(target.month),
        "lag_1":  _vol_at(target - pd.DateOffset(months=1)),
        "lag_12": _vol_at(target - pd.DateOffset(months=12)),
    }])[FEATURE_COLS]
    # `build_features` returns int32 for the categorical/calendar columns;
    # the model's signature is strict, so the inference row has to match.
    for col in ["plaza_id", "vehicle_id", "direction_id", "year", "month"]:
        row[col] = row[col].astype("int32")
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plaza", required=True)
    parser.add_argument("--direction", required=True)
    parser.add_argument("--vehicle", required=True)
    parser.add_argument("--month", required=True, help="e.g. 2020-01")
    args = parser.parse_args()

    x = _build_row(args.plaza, args.direction, args.vehicle, args.month)

    model = mlflow.pyfunc.load_model(MODEL_URI)
    forecast = model.predict(x)[0]
    print(f"Forecast: {int(forecast)} vehicles")


if __name__ == "__main__":
    main()
