import math
import logging
import duckdb
from typing import Dict, Any, List, Optional
from app.session_manager import Session
from app.schemas import ChatMessageResponse
from app.llm_service import generate_sql_query
from app.sql_validator import validate_and_clean_sql
from app.chart_generator import generate_echarts_options

logger = logging.getLogger("datavera.query_engine")

def process_chat_query(
    session: Session,
    question: str,
    provider: Optional[str] = None
) -> ChatMessageResponse:
    conn = session.get_connection()
    table_name = session.table_name

    # 1. Inspect table schema and sample rows
    try:
        describe_rows = conn.execute(f"DESCRIBE {table_name}").fetchall()
        schema_info = "\n".join([f"- {col[0]} ({col[1]})" for col in describe_rows])

        sample_df = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").df()
        sample_rows_str = sample_df.to_string(index=False)
    except Exception as e:
        return ChatMessageResponse(
            question=question,
            sql="",
            explanation="",
            results=[],
            columns=[],
            row_count=0,
            chart_recommended=False,
            error=f"Aucune table de données active. Veuillez d'abord importer un fichier CSV ou Excel."
        )

    # 2. First attempt SQL generation
    raw_sql, explanation = generate_sql_query(schema_info, sample_rows_str, question, provider)

    # Validate SQL security
    is_valid, clean_sql, error_msg = validate_and_clean_sql(raw_sql)
    if not is_valid:
        return ChatMessageResponse(
            question=question,
            sql=raw_sql,
            explanation=explanation,
            results=[],
            columns=[],
            row_count=0,
            chart_recommended=False,
            error=f"Sécurité : {error_msg}"
        )

    # 3. Execute SQL with 1-retry auto-correction on DuckDB execution error
    results: List[Dict[str, Any]] = []
    columns: List[str] = []
    executed_sql = clean_sql
    exec_error: Optional[str] = None

    try:
        rel = conn.execute(executed_sql)
        columns = [desc[0] for desc in rel.description] if rel.description else []
        df = rel.df()
        df = df.map(lambda v: None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
        results = df.to_dict(orient="records")
    except Exception as err:
        exec_error = str(err)
        logger.warning(f"SQL Execution failed: {exec_error}. Retrying with error feedback...")

        # Automatic retry step: Feed DuckDB error back to LLM
        retry_raw_sql, retry_explanation = generate_sql_query(
            schema_info, sample_rows_str, question, provider, error_feedback=exec_error
        )
        is_valid_retry, clean_retry_sql, retry_val_err = validate_and_clean_sql(retry_raw_sql)

        if is_valid_retry:
            try:
                rel = conn.execute(clean_retry_sql)
                columns = [desc[0] for desc in rel.description] if rel.description else []
                df = rel.df()
                df = df.map(lambda v: None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v)
                results = df.to_dict(orient="records")
                executed_sql = clean_retry_sql
                explanation = retry_explanation
                exec_error = None
            except Exception as second_err:
                exec_error = f"Erreur d'exécution DuckDB: {str(second_err)}"
        else:
            exec_error = f"Erreur de validation après retentative: {retry_val_err}"

    if exec_error:
        return ChatMessageResponse(
            question=question,
            sql=executed_sql,
            explanation=explanation,
            results=[],
            columns=[],
            row_count=0,
            chart_recommended=False,
            error=exec_error
        )

    # 4. Generate ECharts Option if suitable
    chart_recommended, chart_type, chart_options = generate_echarts_options(
        question, results, columns
    )

    return ChatMessageResponse(
        question=question,
        sql=executed_sql,
        explanation=explanation,
        results=results,
        columns=columns,
        row_count=len(results),
        chart_recommended=chart_recommended,
        chart_type=chart_type,
        chart_options=chart_options,
        error=None
    )
