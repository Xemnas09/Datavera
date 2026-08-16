import math
import duckdb
from typing import List, Dict, Any
from app.session_manager import Session
from app.schemas import DatasetProfile, ColumnProfile

def profile_dataset(session: Session, file_size_bytes: int) -> DatasetProfile:
    conn = session.get_connection()
    table_name = session.table_name

    # 1. Get total row count
    row_count_res = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    row_count = row_count_res[0] if row_count_res else 0

    # 2. Get column info
    columns_info = conn.execute(f"DESCRIBE {table_name}").fetchall()
    column_count = len(columns_info)

    # Fetch sample rows (top 100)
    sample_df = conn.execute(f"SELECT * FROM {table_name} LIMIT 100").df()
    # Sanitize NaNs and infinite values for JSON serialization
    sample_df = sample_df.map(lambda v: None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
    sample_rows = sample_df.to_dict(orient="records")

    columns_profile: List[ColumnProfile] = []

    for col_info in columns_info:
        col_name = col_info[0]
        col_type = str(col_info[1])

        # Escape column name in SQL identifier
        col_escaped_str = col_name.replace('"', '""')
        escaped_col = f'"{col_escaped_str}"'

        # Null count
        null_res = conn.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {escaped_col} IS NULL").fetchone()
        null_count = null_res[0] if null_res else 0
        null_percentage = round((null_count / row_count * 100), 2) if row_count > 0 else 0.0

        # Distinct value count
        unique_res = conn.execute(f"SELECT COUNT(DISTINCT {escaped_col}) FROM {table_name}").fetchone()
        unique_count = unique_res[0] if unique_res else 0

        # Get up to 5 non-null sample values
        samples_res = conn.execute(f"SELECT DISTINCT {escaped_col} FROM {table_name} WHERE {escaped_col} IS NOT NULL LIMIT 5").fetchall()
        sample_vals = [r[0] for r in samples_res]

        stats: Dict[str, Any] = {}
        # Numeric stats if column is numeric
        is_numeric = any(t in col_type.upper() for t in ['INT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC', 'HUGEINT', 'TINYINT', 'SMALLINT', 'BIGINT', 'REAL'])
        if is_numeric and row_count > 0:
            try:
                num_stats = conn.execute(
                    f"SELECT MIN({escaped_col}), MAX({escaped_col}), AVG({escaped_col}), STDDEV_SAMP({escaped_col}), MEDIAN({escaped_col}) FROM {table_name}"
                ).fetchone()
                if num_stats:
                    def safe_val(val):
                        if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
                            return None
                        return round(float(val), 4) if isinstance(val, (int, float)) else val

                    stats = {
                        "min": safe_val(num_stats[0]),
                        "max": safe_val(num_stats[1]),
                        "avg": safe_val(num_stats[2]),
                        "stddev": safe_val(num_stats[3]),
                        "median": safe_val(num_stats[4])
                    }
            except Exception:
                stats = {}

        columns_profile.append(
            ColumnProfile(
                name=col_name,
                data_type=col_type,
                null_count=null_count,
                null_percentage=null_percentage,
                unique_count=unique_count,
                sample_values=sample_vals,
                stats=stats if stats else None
            )
        )

    return DatasetProfile(
        filename=session.dataset_filename or "data.csv",
        file_size_bytes=file_size_bytes,
        row_count=row_count,
        column_count=column_count,
        columns=columns_profile,
        sample_rows=sample_rows,
        table_name=table_name
    )
