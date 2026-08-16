import pytest
import os
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.session_manager import session_manager, Session
from app.ingestion import ingest_file_to_session
from app.profiling import profile_dataset

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_session_creation():
    response = client.get("/api/session")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["has_dataset"] is False

def test_sample_datasets_list():
    response = client.get("/api/samples")
    assert response.status_code == 200
    samples = response.json()
    assert len(samples) >= 2
    sample_ids = [s["id"] for s in samples]
    assert "sales" in sample_ids
    assert "hr" in sample_ids

def test_load_sample_dataset():
    # Get session
    session_res = client.get("/api/session")
    session_id = session_res.json()["session_id"]

    response = client.post(f"/api/samples/sales", headers={"x-session-id": session_id})
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["profile"]["row_count"] == 15
    assert data["profile"]["column_count"] == 10
    assert len(data["profile"]["columns"]) == 10
    assert len(data["profile"]["sample_rows"]) == 15

def test_file_upload_csv():
    csv_content = "nom,age,ville,salaire\nAlice,30,Paris,45000\nBob,25,Lyon,38000\nCharlie,35,Marseille,52000\n"

    with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tmp:
        tmp.write(csv_content)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.csv", f, "text/csv")}
            )
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["row_count"] == 3
        assert data["profile"]["column_count"] == 4

        # Check column stats for numeric age & salaire
        age_col = next(c for c in data["profile"]["columns"] if c["name"] == "age")
        assert age_col["stats"]["min"] == 25.0
        assert age_col["stats"]["max"] == 35.0
        assert age_col["stats"]["avg"] == 30.0
    finally:
        os.unlink(tmp_path)
