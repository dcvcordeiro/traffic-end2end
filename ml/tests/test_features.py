"""Integration smoke test for `build_features`.

These tests run against the live `gold` schema in the Docker stack — they
are not unit tests. They exist to catch the most common breakages early:

- Gold tables missing or renamed (the Day 1 contract drifted)
- Column types changed (lag_1 came back as a string)
- Lag features all null (groupby key incorrect)
"""
from __future__ import annotations

import pytest

from ml.features import FEATURE_COLS, TARGET_COL, build_features


@pytest.mark.integration
def test_build_features_returns_non_empty_matrix():
    df = build_features()
    assert len(df) > 0, "feature matrix is empty — check the Gold layer"


@pytest.mark.integration
def test_build_features_has_expected_columns():
    df = build_features()
    expected = set(FEATURE_COLS) | {TARGET_COL, "month_start"}
    missing = expected - set(df.columns)
    assert not missing, f"missing columns: {missing}"


@pytest.mark.integration
def test_lag_features_have_no_nulls():
    df = build_features()
    assert df["lag_1"].isna().sum() == 0
    assert df["lag_12"].isna().sum() == 0
