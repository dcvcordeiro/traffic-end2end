"""Unit tests for `ml.split.time_split`."""
from __future__ import annotations

import pandas as pd
import pytest

from ml.split import time_split


def _make_df(months: int) -> pd.DataFrame:
    return pd.DataFrame({
        "month_start": pd.date_range("2018-01-01", periods=months, freq="MS"),
        "value": list(range(months)),
    })


def test_holds_out_last_six_months():
    df = _make_df(24)
    train, test = time_split(df, holdout_months=6)
    assert len(train) == 18
    assert len(test) == 6
    assert train["month_start"].max() < test["month_start"].min()


def test_does_not_mutate_input():
    df = _make_df(12)
    df_copy = df.copy()
    _ = time_split(df, holdout_months=3)
    pd.testing.assert_frame_equal(df, df_copy)


def test_rejects_zero_holdout():
    df = _make_df(12)
    with pytest.raises(ValueError):
        time_split(df, holdout_months=0)


def test_rejects_missing_date_col():
    df = pd.DataFrame({"value": [1, 2, 3]})
    with pytest.raises(KeyError):
        time_split(df, holdout_months=2)


def test_custom_date_col():
    df = _make_df(12).rename(columns={"month_start": "ym"})
    train, test = time_split(df, holdout_months=2, date_col="ym")
    assert len(train) == 10
    assert len(test) == 2
