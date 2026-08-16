import pytest
import os
import tempfile
import pandas as pd
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_excel_file_upload():
    # Create sample Excel DataFrame
    df = pd.DataFrame({
        "produit": ["Téléphone", "Ordinateur", "Tablette"],
        "prix": [499.99, 1299.50, 299.00],
        "stock": [50, 20, 100]
    })

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        df.to_excel(tmp.name, index=False)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("inventaire.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            )
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["row_count"] == 3
        assert data["profile"]["column_count"] == 3
        assert data["profile"]["filename"] == "inventaire.xlsx"

        # Test querying the excel dataset
        session_id = data["session_id"]
        q_res = client.post(
            "/api/query",
            json={"question": "Quel est le produit le plus cher ?"},
            headers={"x-session-id": session_id}
        )
        assert q_res.status_code == 200
        q_data = q_res.json()
        assert q_data["row_count"] >= 1
        assert q_data["error"] is None
    finally:
        os.unlink(tmp_path)
