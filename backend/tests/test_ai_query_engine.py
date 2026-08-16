import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.sql_validator import validate_and_clean_sql
from app.chart_generator import generate_echarts_options

client = TestClient(app)

def test_sql_validator_valid_select():
    valid, clean_sql, err = validate_and_clean_sql("SELECT * FROM dataset WHERE age > 20")
    assert valid is True
    assert err is None
    assert "LIMIT 1000" in clean_sql

def test_sql_validator_blocks_destructive_commands():
    # DROP
    valid, _, err = validate_and_clean_sql("DROP TABLE dataset")
    assert valid is False
    assert "Commande SQL non autorisée" in err

    # DELETE
    valid, _, err = validate_and_clean_sql("DELETE FROM dataset WHERE id = 1")
    assert valid is False
    assert "Commande SQL non autorisée" in err

    # UPDATE
    valid, _, err = validate_and_clean_sql("UPDATE dataset SET age = 30")
    assert valid is False
    assert "Commande SQL non autorisée" in err

    # ATTACH / COPY
    valid, _, err = validate_and_clean_sql("COPY dataset TO 'file.csv'")
    assert valid is False
    assert "Commande SQL non autorisée" in err

def test_chart_generator_bar():
    results = [
        {"categorie": "Électronique", "total_ca": 5000.0},
        {"categorie": "Mobilier", "total_ca": 3200.0},
        {"categorie": "Services", "total_ca": 6100.0}
    ]
    columns = ["categorie", "total_ca"]
    rec, chart_type, options = generate_echarts_options("Total CA par catégorie", results, columns)
    assert rec is True
    assert chart_type == "bar"
    assert "series" in options
    assert options["xAxis"]["data"] == ["Électronique", "Mobilier", "Services"]

def test_end_to_end_query_execution():
    # Load sample dataset
    sess_res = client.get("/api/session")
    session_id = sess_res.json()["session_id"]

    load_res = client.post("/api/samples/sales", headers={"x-session-id": session_id})
    assert load_res.status_code == 200

    # Query with natural language question
    query_res = client.post(
        "/api/query",
        json={"question": "Combien y a-t-il de commandes au total ?"},
        headers={"x-session-id": session_id}
    )
    assert query_res.status_code == 200
    data = query_res.json()
    assert "sql" in data
    assert "explanation" in data
    assert data["row_count"] >= 1
    assert data["error"] is None
