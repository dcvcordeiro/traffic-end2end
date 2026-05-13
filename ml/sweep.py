"""Step 3 sweep: log six configurations as separate runs.

Each configuration is one MLflow run inside the `forecast-traffic-volume`
experiment. You finish this file by writing the per-config training loop.
The TODO marks the only block that needs your code.

Run with:
    make sweep
"""
from __future__ import annotations

import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from ml.features import FEATURE_COLS, TARGET_COL, build_features
from ml.split import time_split

EXPERIMENT_NAME = "forecast-traffic-volume"

# Six configurations: 3 × n_estimators × 2 × max_depth.
SWEEP_CONFIGS = [
    {"n_estimators":  50, "max_depth":  5, "random_state": 42},
    {"n_estimators":  50, "max_depth": 10, "random_state": 42},
    {"n_estimators": 100, "max_depth":  5, "random_state": 42},
    {"n_estimators": 100, "max_depth": 10, "random_state": 42},
    {"n_estimators": 200, "max_depth":  5, "random_state": 42},
    {"n_estimators": 200, "max_depth": 10, "random_state": 42},
]


def _prepare():
    df = build_features()
    train, test = time_split(df, holdout_months=6)
    return (
        train[FEATURE_COLS], train[TARGET_COL],
        test[FEATURE_COLS],  test[TARGET_COL],
    )


def main():
    mlflow.set_experiment(EXPERIMENT_NAME)
    x_train, y_train, x_test, y_test = _prepare()
    # MLflow infers the model signature from a small input example.
    input_example = x_test.head(5)

    for i, params in enumerate(SWEEP_CONFIGS, start=1):
        run_name = f"config-{i}"

        with mlflow.start_run(run_name=run_name):
            model = RandomForestRegressor(**params)
            model.fit(x_train, y_train)
            preds = model.predict(x_test)
            mae = float(mean_absolute_error(y_test, preds))
            rmse = float(root_mean_squared_error(y_test, preds))
            mean_volume = float(y_test.mean())
            mlflow.log_params(params)
            mlflow.log_metrics({"mae": mae, "rmse": rmse, "mean_volume": mean_volume})
            mlflow.sklearn.log_model(
                model, name="model", input_example=input_example,
            )

    print(f"Logged {len(SWEEP_CONFIGS)} runs. Open the UI to compare.")


if __name__ == "__main__":
    main()
