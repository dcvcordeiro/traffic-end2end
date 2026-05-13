"""Step 4 promotion gate: register the challenger only if it beats the champion.

Reads the sweep results from the `forecast-traffic-volume` experiment,
finds the best configuration (lowest MAE), and compares it against the
run currently behind the `@production` alias. If the challenger wins,
register the challenger's model and move the alias; otherwise leave the
champion in place.

This file has ONE TODO — and it is the most important line of the day.
You are picking the *comparator direction*: lower MAE is better. Get
this wrong and the gate will either block every challenger forever or
promote every challenger regardless of quality.

Run with:
    make promote
"""
from __future__ import annotations

import mlflow
from mlflow.client import MlflowClient
from mlflow.exceptions import RestException

EXPERIMENT_NAME = "forecast-traffic-volume"
REGISTERED_MODEL_NAME = "ForecastTrafficVolume"
PRODUCTION_ALIAS = "production"


def _best_challenger(client: MlflowClient):
    """Return the run from the experiment with the lowest test MAE."""
    exp = client.get_experiment_by_name(EXPERIMENT_NAME)
    if exp is None:
        raise RuntimeError(f"Experiment {EXPERIMENT_NAME!r} not found")
    runs = client.search_runs(
        [exp.experiment_id],
        order_by=["metrics.mae ASC"],
        max_results=1,
    )
    if not runs:
        raise RuntimeError(f"No runs found in experiment {EXPERIMENT_NAME!r}")
    return runs[0]


def _current_champion(client: MlflowClient):
    """Return the run behind the current @production alias, or None."""
    try:
        mv = client.get_model_version_by_alias(
            REGISTERED_MODEL_NAME, PRODUCTION_ALIAS
        )
    except RestException:
        return None
    return client.get_run(mv.run_id)


def _logged_model_uri(client: MlflowClient, run) -> str:
    """Return the `models:/m-<id>` URI for the model logged inside `run`.

    MLflow 3.x stores logged models as their own entities, separate from
    run artifacts. Passing this URI to `register_model` avoids the
    `runs:/{run_id}/model` fallback path (which prints a warning).
    """
    logged = client.search_logged_models(
        experiment_ids=[run.info.experiment_id],
        filter_string=f"source_run_id='{run.info.run_id}'",
        max_results=1,
    )
    if not logged:
        raise RuntimeError(f"No logged model for run {run.info.run_id}")
    return f"models:/{logged[0].model_id}"


def challenger_wins(challenger_mae: float, champion_mae: float) -> bool:
    """Return True if the challenger should replace the champion.

    The metric here is MAE — Mean Absolute Error in vehicles/month.

    TODO (Step 4): replace the body of this function with the correct
    comparison. In Session 5's airline lab the rule was "higher F1 wins":
        return challenger_f1 > champion_f1
    The metric here flips: *lower* MAE wins. Pick the right operator and
    return the result. Get this wrong and the gate is broken.
    """
    raise NotImplementedError(
        "Step 4 — fill in `challenger_wins` in ml/promote.py"
    )


def main():
    client = MlflowClient()
    challenger = _best_challenger(client)
    champion = _current_champion(client)

    challenger_mae = challenger.data.metrics["mae"]
    champion_mae = (
        champion.data.metrics["mae"] if champion is not None else float("inf")
    )

    print(f"Champion   MAE: {champion_mae:.2f}")
    print(f"Challenger MAE: {challenger_mae:.2f}")

    if challenger_wins(challenger_mae, champion_mae):
        mv = mlflow.register_model(
            _logged_model_uri(client, challenger),
            REGISTERED_MODEL_NAME,
        )
        client.set_registered_model_alias(
            name=REGISTERED_MODEL_NAME,
            alias=PRODUCTION_ALIAS,
            version=mv.version,
        )
        print(
            f"Challenger wins. "
            f"{REGISTERED_MODEL_NAME} v{mv.version} -> {PRODUCTION_ALIAS}"
        )
    else:
        print("Champion holds. No promotion.")


if __name__ == "__main__":
    main()
