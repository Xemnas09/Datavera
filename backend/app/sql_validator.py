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

    # Parse with sqlglot for DuckDB dialect first
    try:
        parsed = sqlglot.parse_one(cleaned_sql, read="duckdb")
    except Exception as e:
        # Fallback if AST parser encounters non-standard syntax: query must start with SELECT or WITH
        if not cleaned_sql.upper().startswith("SELECT") and not cleaned_sql.upper().startswith("WITH"):
            return False, cleaned_sql, "La requête SQL doit commencer par SELECT ou WITH."
        parsed = None

    if parsed is not None:
        # AST Inspection: verify that no statement or AST node is a forbidden destructive expression
        forbidden_classes = (
            exp.Drop, exp.Delete, exp.Update, exp.Insert, exp.Alter, exp.Create,
            exp.Copy, exp.TruncateTable, exp.Command
        )
        for node in parsed.walk():
            if isinstance(node, forbidden_classes):
                return False, cleaned_sql, f"Commande SQL non autorisée détectée ('{node.key.upper()}'). Seules les requêtes SELECT en lecture seule sont permises."

        # Ensure top-level expression is SELECT or WITH
        if not isinstance(parsed, (exp.Select, exp.With)):
            return False, cleaned_sql, f"Commande SQL non autorisée détectée ('{type(parsed).__name__.upper()}'). Seules les requêtes SELECT en lecture seule sont permises."
    else:
        # Check forbidden keywords outside quotes as fallback
        sql_no_strings = re.sub(r"'[^']*'", "''", cleaned_sql)
        for kw in FORBIDDEN_KEYWORDS:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, sql_no_strings, re.IGNORECASE):
                return False, cleaned_sql, f"Commande SQL non autorisée détectée ('{kw}'). Seules les requêtes SELECT en lecture seule sont permises."

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
