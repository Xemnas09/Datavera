import pytest
import os
import tempfile
import pandas as pd
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.session_manager import session_manager
from app.ingestion_v2 import (
    detect_file_format_and_magic_bytes,
    sniff_csv_delimiter_and_encoding,
    score_header_candidates,
    sanitize_dataframe,
    ingest_file_v2
)

client = TestClient(app)

def test_magic_bytes_mismatch_detection():
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(b"col1,col2\nval1,val2\n")
        tmp_path = Path(tmp.name)

    try:
        actual_format, warnings = detect_file_format_and_magic_bytes(tmp_path, "test.xlsx")
        assert actual_format == "csv"
        assert len(warnings) >= 1
        assert "extension" in warnings[0].lower()
    finally:
        os.unlink(tmp_path)

def test_csv_delimiter_sniffing_semicolon():
    csv_data = "Nom;Age;Ville;Salaire\nAlice;30;Paris;45 000\nBob;25;Lyon;38 000\n"
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="wb", delete=False) as tmp:
        tmp.write(csv_data.encode("utf-8"))
        tmp_path = Path(tmp.name)

    try:
        encoding, delimiter, warnings = sniff_csv_delimiter_and_encoding(tmp_path)
        assert delimiter == ";"
        assert encoding == "utf-8"
        assert any("point-virgule" in w for w in warnings)
    finally:
        os.unlink(tmp_path)

def test_french_regional_numbers_and_missing_values():
    df = pd.DataFrame({
        "Produit": ["A", "B", "C", "D"],
        "Montant": ["1 234,56", "2 500,00", "N/A", "500,25"],
        "Code": ["#DIV/0!", "OK", "-", "n/d"]
    })

    clean_df, warnings = sanitize_dataframe(df)

    assert clean_df["Montant"].iloc[0] == 1234.56
    assert clean_df["Montant"].iloc[1] == 2500.00
    assert pd.isna(clean_df["Montant"].iloc[2])

    assert pd.isna(clean_df["Code"].iloc[0])
    assert pd.isna(clean_df["Code"].iloc[2])
    assert pd.isna(clean_df["Code"].iloc[3])

def test_intercalated_subtotal_rows_stripping():
    df = pd.DataFrame({
        "Categorie": ["Électronique", "Mobilier", "Sous-total Mobilier", "Services", "Total Général"],
        "Ventes": [100, 200, 200, 300, 600]
    })

    clean_df, warnings = sanitize_dataframe(df)
    assert len(clean_df) == 3
    assert "Sous-total Mobilier" not in clean_df["Categorie"].values
    assert "Total Général" not in clean_df["Categorie"].values
    assert any("ligne(s) de total/sous-total" in w for w in warnings)

def test_duplicate_and_unnamed_column_renaming():
    df = pd.DataFrame([
        [1, 2, 3, 4]
    ], columns=["Nom", "Nom", None, "Nom_Spécial@Char!"])

    clean_df, warnings = sanitize_dataframe(df)
    cols = list(clean_df.columns)
    assert cols[0] == "Nom"
    assert cols[1] == "Nom_1"
    assert cols[2] == "Colonne_3"
    assert "Nom_Spécial_Char_" in cols[3]

def test_excel_serial_date_conversion():
    df = pd.DataFrame({
        "ID": [101, 102],
        "Date_Embauche": [44562, 44563]
    })

    clean_df, warnings = sanitize_dataframe(df)
    assert clean_df["Date_Embauche"].iloc[0] == "2022-01-01"
    assert clean_df["Date_Embauche"].iloc[1] == "2022-01-02"

def test_end_to_end_robust_ingestion_api():
    csv_content = "Rapport Annuel Ventes\nLigne de garde à ignorer\nid;client;montant\n101;TechCorp;1 500,00\n102;DataConsult;N/A\nSous-total;Total;1 500,00\n"
    with tempfile.NamedTemporaryFile(suffix=".csv", mode="wb", delete=False) as tmp:
        tmp.write(csv_content.encode("utf-8"))
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("ventes.csv", f, "text/csv")}
            )
        assert response.status_code == 200
        data = response.json()

        assert "warnings" in data
        assert len(data["warnings"]) >= 1
        assert data["profile"]["row_count"] == 2

        sess_id = data["session_id"]
        config_res = client.post(
            "/api/upload/configure",
            json={"header_index": 2, "delimiter": ";"},
            headers={"x-session-id": sess_id}
        )
        assert config_res.status_code == 200
        config_data = config_res.json()
        assert config_data["profile"]["row_count"] == 2
    finally:
        os.unlink(tmp_path)
