import os
import tempfile
import pandas as pd
import polars as pl
import duckdb
from pathlib import Path
from typing import Tuple, Dict, Any
from app.session_manager import Session

def ingest_file_to_session(session: Session, file_path: Path, filename: str) -> str:
    """
    Ingests a CSV, TSV, or Excel file into the session's DuckDB instance.
    Returns the table name ('dataset').
    """
    conn = session.get_connection()
    table_name = "dataset"

    # Drop existing dataset table if present
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")

    ext = file_path.suffix.lower()

    if ext in ['.csv', '.tsv', '.txt']:
        # DuckDB native CSV reader (fast & memory efficient for large datasets)
        # Handles separator detection automatically
        conn.execute(
            f"CREATE TABLE {table_name} AS SELECT * FROM read_csv_auto('{file_path}', normalize_names=False, header=True)"
        )
    elif ext in ['.xlsx', '.xls']:
        # Read excel via pandas / openpyxl then register into DuckDB
        df = pd.read_excel(file_path)
        # Register pandas dataframe and copy into persistent DuckDB table
        conn.register("temp_excel_df", df)
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM temp_excel_df")
        conn.unregister("temp_excel_df")
    else:
        raise ValueError(f"Format de fichier non supporté: {ext}. Formats supportés: CSV, TSV, XLSX, XLS")

    session.dataset_filename = filename
    session.table_name = table_name
    return table_name
