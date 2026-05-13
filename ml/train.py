"""Step 1 + Step 2 trainer for the traffic-volume forecasting task.

You finish this file in Steps 1 and 2 of Block 3. The data loading, the
train/test split, the model fit, and the metric calculation are all
pre-baked. Your job is to add the MLflow calls in the two `# TODO`
blocks.

Run with:
    make train-once         # Step 1: a single tracked run
    make register           # Step 2: also register and alias the model
"""
from __future__ import annotations

import argparse

import mlflow
import mlflow.sklearn
from mlflow.client import MlflowClient
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from ml.features import FEATURE_COLS, TARGET_COL, build_features
from ml.split import time_split

EXPERIMENT_NAME = "forecast-traffic-volume"
REGISTERED_MODEL_NAME = "ForecastTrafficVolume"
PRODUCTION_ALIAS = "production"

PARAMS_CHOICES = {
    "canonical": {"n_estimators": 100, "max_depth": 10, "random_state": 42},
    "small":     {"n_estimators":  50, "max_depth":  5, "random_state": 42},
    "deep":      {"n_estimators": 100, "max_depth": 20, "random_state": 42},
    "big":       {"n_estimators": 300, "max_depth": 10, "random_state": 42},
}


def _prepare():
    df = build_features()
    train, test = time_split(df, holdout_months=6)
    return (
        train[FEATURE_COLS], train[TARGET_COL],
        test[FEATURE_COLS],  test[TARGET_COL],
    )


def _fit_and_score(params: dict):
    x_train, y_train, x_test, y_test = _prepare()
    model = RandomForestRegressor(**params)
    model.fit(x_train, y_train)
    preds = model.predict(x_test)
    metrics = {
        "mae":         float(mean_absolute_error(y_test, preds)),
        "rmse":        float(root_mean_squared_error(y_test, preds)),
        "mean_volume": float(y_test.mean()),
    }
    # A small slice of the test set is enough for MLflow to infer the
    # model signature (column names + dtypes) at log time.
    input_example = x_test.head(5)
    return model, metrics, input_example


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--register", action="store_true",
        help="Also register the model and assign @production",
    )
    parser.add_argument(
        "--params", default="canonical",
        choices=list(PARAMS_CHOICES.keys()),
    )
    args = parser.parse_args()

    params = PARAMS_CHOICES[args.params]
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run():
        model, metrics, input_example = _fit_and_score(params)
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        model_info = mlflow.sklearn.log_model(
            model, name="model", input_example=input_example,
        )

    if args.register:
        mv = mlflow.register_model(model_info.model_uri, REGISTERED_MODEL_NAME)
        MlflowClient().set_registered_model_alias(
            name=REGISTERED_MODEL_NAME,
            alias=PRODUCTION_ALIAS,
            version=mv.version,
        )
        print(f"@production currently points to version {mv.version}")


if __name__ == "__main__":
    main()
