import re
import sqlglot
from sqlglot import exp
from typing import Tuple, Optional
from app.config import MAX_ROW_LIMIT

FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
    "COPY", "ATTACH", "DETACH", "VACUUM", "PRAGMA", "EXEC",
    "INSTALL", "LOAD", "EXPORT", "IMPORT", "TRUNCATE", "RENAME",
    "GRANT", "REVOKE"
]

def validate_and_clean_sql(sql: str) -> Tuple[bool, str, Optional[str]]:
    """
    Validates that a SQL query is strictly read-only and safe to execute.
    Returns: (is_valid, cleaned_sql, error_message)
    """
    if not sql or not sql.strip():
        return False, "", "La requête SQL fournie est vide."

    cleaned_sql = sql.strip().rstrip(';')

    # Check forbidden keywords (case insensitive regex word boundaries)
    for kw in FORBIDDEN_KEYWORDS:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, cleaned_sql, re.IGNORECASE):
            return False, cleaned_sql, f"Commande SQL non autorisée détectée ('{kw}'). Seules les requêtes SELECT en lecture seule sont permises."

    # Parse with sqlglot for DuckDB dialect
    try:
        parsed = sqlglot.parse_one(cleaned_sql, read="duckdb")
    except Exception as e:
        # Fallback keyword checks if AST parser encounters non-standard syntax
        if not cleaned_sql.upper().startswith("SELECT") and not cleaned_sql.upper().startswith("WITH"):
            return False, cleaned_sql, "La requête SQL doit commencer par SELECT ou WITH."
        parsed = None

    if parsed is not None:
        # Ensure top-level expression is SELECT or WITH
        if not isinstance(parsed, (exp.Select, exp.With)):
            return False, cleaned_sql, f"Type de requête non autorisé ({type(parsed).__name__}). Seules les requêtes SELECT/WITH sont autorisées."

    # Enforce LIMIT on query if not already present
    if not re.search(r'\bLIMIT\s+\d+', cleaned_sql, re.IGNORECASE):
        cleaned_sql = f"{cleaned_sql} LIMIT {MAX_ROW_LIMIT}"
    else:
        # Check existing limit doesn't exceed MAX_ROW_LIMIT
        match = re.search(r'\bLIMIT\s+(\d+)', cleaned_sql, re.IGNORECASE)
        if match:
            limit_val = int(match.group(1))
            if limit_val > MAX_ROW_LIMIT:
                cleaned_sql = re.sub(
                    r'\bLIMIT\s+\d+',
                    f"LIMIT {MAX_ROW_LIMIT}",
                    cleaned_sql,
                    flags=re.IGNORECASE
                )

    return True, cleaned_sql, None
