import pytest
import pandas as pd
import numpy as np
from app.column_classifier import (
    classify_dataframe,
    classify_column,
    validate_chart_config,
    ChartValidationResult,
    ColumnClassification
)

def test_classify_column_numeric():
    # Non-monotonic series with 30 distinct values to avoid identifier heuristics & low cardinality threshold
    series = pd.Series([10.5, 20.3, 5.1, 40.8, 12.2, 60.4, 3.9, 80.1, 15.3, 100.2] * 3)
    cls = classify_column(series, "chiffre_affaires")
    assert cls.inferred_type == "numeric"
    assert cls.confidence >= 0.8

def test_classify_column_identifier():
    series = pd.Series([1001, 1002, 1003, 1004, 1005, 1006, 1007])
    cls = classify_column(series, "id_client")
    assert cls.inferred_type == "identifier"
    assert cls.confidence >= 0.5

def test_classify_column_categorical():
    series = pd.Series(["Électronique", "Mobilier", "Services", "Électronique", "Mobilier"])
    cls = classify_column(series, "categorie")
    assert cls.inferred_type == "categorical"

def test_validate_chart_config_bar_valid():
    df = pd.DataFrame({
        "cat": ["A", "B", "C", "A"],
        "val": [10.5, 20.0, 30.5, 10.5]
    })
    classifications = {
        "cat": ColumnClassification(name="cat", dtype_pandas="object", inferred_type="categorical", confidence=1.0, cardinality=3, cardinality_ratio=0.75),
        "val": ColumnClassification(name="val", dtype_pandas="float64", inferred_type="numeric", confidence=1.0, cardinality=3, cardinality_ratio=0.75)
    }
    res = validate_chart_config(df, "bar", {"x": "cat", "y": "val"}, classifications=classifications)
    assert res.is_valid is True
    assert len(res.errors) == 0

def test_validate_chart_config_pie_negative_error():
    df = pd.DataFrame({
        "cat": ["A", "B", "C", "A"],
        "val": [10.0, -5.0, 30.0, 10.0]
    })
    classifications = {
        "cat": ColumnClassification(name="cat", dtype_pandas="object", inferred_type="categorical", confidence=1.0, cardinality=3, cardinality_ratio=0.75),
        "val": ColumnClassification(name="val", dtype_pandas="float64", inferred_type="numeric", confidence=1.0, cardinality=3, cardinality_ratio=0.75)
    }
    res = validate_chart_config(df, "pie", {"category": "cat", "value": "val"}, classifications=classifications)
    assert res.is_valid is False
    assert any("négatives" in err for err in res.errors)
    assert res.suggestion is not None
