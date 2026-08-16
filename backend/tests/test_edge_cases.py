import pytest
import pandas as pd
import numpy as np
from app.column_classifier import (
    classify_dataframe,
    classify_column,
    validate_chart_config,
    CHART_RULES
)

def test_single_row_dataset():
    df = pd.DataFrame({"cat": ["A"], "val": [10.0]})
    classifications = classify_dataframe(df)
    assert "cat" in classifications
    assert "val" in classifications

    # Validation should fail or warn gracefully for single row
    res = validate_chart_config(df, "density", {"x": "val"}, classifications)
    assert res.is_valid is False or len(res.warnings) > 0

def test_constant_column():
    series = pd.Series([5.0] * 50)
    cls = classify_column(series, "constante")
    assert cls.cardinality == 1
    assert cls.cardinality_ratio == 0.02

def test_high_missing_values():
    vals = [10.0] * 5 + [np.nan] * 95
    series = pd.Series(vals)
    cls = classify_column(series, "valeurs_manquantes")
    assert cls.inferred_type in ["numeric", "categorical"]

def test_all_16_chart_validations():
    df = pd.DataFrame({
        "cat1": ["A", "B", "C", "D", "E"],
        "cat2": ["X", "Y", "Z", "W", "V"],
        "num1": [10.0, 20.0, 30.0, 40.0, 50.0],
        "num2": [1.0, 2.0, 3.0, 4.0, 5.0],
        "num3": [100.0, 200.0, 300.0, 400.0, 500.0],
        "date1": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
    })
    classifications = classify_dataframe(df)

    for chart_type in CHART_RULES.keys():
        # Test basic mapping call without throwing unhandled exceptions
        mapping = {}
        if chart_type in ("bar", "pie", "donut", "treemap", "bar_sorted"):
            mapping = {"category": "cat1", "value": "num1"}
        elif chart_type in ("bar_grouped", "bar_stacked", "bar_100pct"):
            mapping = {"category": "cat1", "series": "cat2", "value": "num1"}
        elif chart_type in ("histogram", "density", "box", "violin"):
            mapping = {"x": "num1"}
        elif chart_type == "scatter":
            mapping = {"x": "num1", "y": "num2"}
        elif chart_type == "bubble":
            mapping = {"x": "num1", "y": "num2", "size": "num3"}
        elif chart_type == "correlation_heatmap":
            mapping = {"x": "num1", "y": "num2"}
        elif chart_type in ("line", "area"):
            mapping = {"x": "date1", "y": "num1"}
        elif chart_type == "area_stacked":
            mapping = {"x": "date1", "category": "cat1", "y": "num1"}

        res = validate_chart_config(df, chart_type, mapping, classifications)
        assert isinstance(res.is_valid, bool)
