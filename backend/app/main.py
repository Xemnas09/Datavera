import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import MAX_UPLOAD_SIZE_BYTES
from app.session_manager import session_manager, Session
from app.ingestion_v2 import ingest_file_v2
from app.profiling import profile_dataset
from app.samples import get_sample_list, get_sample_filepath
from app.query_engine import process_chat_query
from app.schemas import (
    UploadResponse,
    SampleDatasetInfo,
    SessionInfoResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    IngestionConfigRequest,
    ReclassifyColumnRequest,
    ColumnClassificationSchema,
    ChartExploreRequest,
    ChartExploreResponse,
    ChartValidationResultSchema
)
from app.column_classifier import ColumnClassification, validate_chart_config
from app.chart_generator import build_echarts_for_config

app = FastAPI(
    title="Datavera API",
    description="Backend analytique DuckDB et IA pour l'analyse de fichiers de données",
    version="2.0.0"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.logging_config import setup_logging
setup_logging()

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": "Datavera API V2",
        "version": "2.0.0",
        "duckdb": "embedded_active"
    }

@app.get("/api/session", response_model=SessionInfoResponse)
def get_session_info(x_session_id: Optional[str] = Header(None)):
    session, created = session_manager.get_or_create_session(x_session_id)
    conn = session.get_connection()

    has_dataset = False
    row_count = None
    try:
        res = conn.execute("SELECT COUNT(*) FROM dataset").fetchone()
        if res:
            has_dataset = True
            row_count = res[0]
    except Exception:
        has_dataset = False

    return SessionInfoResponse(
        session_id=session.session_id,
        created_at=str(session.created_at),
        last_activity=str(session.last_activity),
        has_dataset=has_dataset,
        dataset_name=session.dataset_filename,
        row_count=row_count
    )

@app.get("/api/samples", response_model=List[SampleDatasetInfo])
def list_sample_datasets():
    return get_sample_list()

@app.post("/api/samples/{sample_id}", response_model=UploadResponse)
def load_sample_dataset(sample_id: str, x_session_id: Optional[str] = Header(None)):
    try:
        file_path, filename = get_sample_filepath(sample_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    session, _ = session_manager.get_or_create_session(x_session_id)

    try:
        ing_res = ingest_file_v2(session, file_path, filename)
        file_size = file_path.stat().st_size
        profile = profile_dataset(session, file_size)

        return UploadResponse(
            session_id=session.session_id,
            message=f"Jeu de données exemple '{filename}' chargé avec succès.",
            profile=profile,
            confidence_score=ing_res.confidence_score,
            requires_user_action=ing_res.requires_user_action,
            detected_header_index=ing_res.detected_header_index,
            selected_sheet=ing_res.selected_sheet,
            available_sheets=ing_res.available_sheets,
            warnings=ing_res.warnings,
            raw_preview_rows=ing_res.raw_preview_rows
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement de l'échantillon: {str(e)}")

@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    x_session_id: Optional[str] = Header(None)
):
    session, _ = session_manager.get_or_create_session(x_session_id)

    temp_dir = Path("/tmp/datavera_uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = temp_dir / f"{session.session_id}_{file.filename}"
    file_size = 0

    try:
        with temp_file_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                file_size += len(chunk)
                if file_size > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Fichier trop volumineux. La taille maximale autorisée est de 150 Mo."
                    )
                buffer.write(chunk)

        # Save temp file path on session for potential configure endpoint call
        session.temp_upload_path = str(temp_file_path)

        ing_res = ingest_file_v2(session, temp_file_path, file.filename)
        profile = profile_dataset(session, file_size)

        return UploadResponse(
            session_id=session.session_id,
            message=f"Fichier '{file.filename}' importé et analysé avec succès.",
            profile=profile,
            confidence_score=ing_res.confidence_score,
            requires_user_action=ing_res.requires_user_action,
            detected_header_index=ing_res.detected_header_index,
            selected_sheet=ing_res.selected_sheet,
            available_sheets=ing_res.available_sheets,
            warnings=ing_res.warnings,
            raw_preview_rows=ing_res.raw_preview_rows
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du fichier: {str(e)}")

@app.post("/api/upload/configure", response_model=UploadResponse)
def reconfigure_ingestion(
    body: IngestionConfigRequest,
    x_session_id: Optional[str] = Header(None)
):
    session = session_manager.get_session(x_session_id)
    if not session or not getattr(session, "temp_upload_path", None) or not Path(session.temp_upload_path).exists():
        raise HTTPException(status_code=404, detail="Aucun fichier d'importation en attente de configuration.")

    temp_path = Path(session.temp_upload_path)
    filename = session.dataset_filename or temp_path.name
    file_size = temp_path.stat().st_size

    try:
        ing_res = ingest_file_v2(
            session,
            temp_path,
            filename,
            selected_sheet=body.sheet_name,
            header_index=body.header_index,
            delimiter=body.delimiter
        )
        profile = profile_dataset(session, file_size)

        return UploadResponse(
            session_id=session.session_id,
            message=f"Importation du fichier '{filename}' reconfigurée avec succès.",
            profile=profile,
            confidence_score=ing_res.confidence_score,
            requires_user_action=False, # User has configured
            detected_header_index=ing_res.detected_header_index,
            selected_sheet=ing_res.selected_sheet,
            available_sheets=ing_res.available_sheets,
            warnings=ing_res.warnings,
            raw_preview_rows=ing_res.raw_preview_rows
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la reconfiguration de l'import: {str(e)}")

@app.post("/api/session/reclassify", response_model=ColumnClassificationSchema)
def reclassify_column(
    body: ReclassifyColumnRequest,
    x_session_id: Optional[str] = Header(None)
):
    session = session_manager.get_session(x_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée.")

    if body.target_type not in ["numeric", "categorical", "identifier", "datetime"]:
        raise HTTPException(status_code=400, detail=f"Type cible invalide: '{body.target_type}'. Types valides: numeric, categorical, identifier, datetime.")

    existing = session.classifications.get(body.column_name)
    dtype_str = existing.dtype_pandas if existing else "object"
    cardinality = existing.cardinality if existing else 0
    cardinality_ratio = existing.cardinality_ratio if existing else 0.0

    updated_cls = ColumnClassificationSchema(
        name=body.column_name,
        dtype_pandas=dtype_str,
        inferred_type=body.target_type,
        confidence=1.0,  # Manual user override
        reasons=[f"Reclassification manuelle par l'utilisateur vers '{body.target_type}'"],
        cardinality=cardinality,
        cardinality_ratio=cardinality_ratio
    )
    session.classifications[body.column_name] = updated_cls
    return updated_cls

@app.post("/api/chart/explore", response_model=ChartExploreResponse)
def explore_chart(
    body: ChartExploreRequest,
    x_session_id: Optional[str] = Header(None)
):
    session = session_manager.get_session(x_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session non trouvée.")

    conn = session.get_connection()
    try:
        df = conn.execute("SELECT * FROM dataset LIMIT 5000").df()
    except Exception:
        raise HTTPException(status_code=400, detail="Aucun jeu de données chargé dans cette session.")

    # Convert session classifications to dataclasses
    cls_dataclasses = {}
    for col_name, cls_schema in session.classifications.items():
        cls_dataclasses[col_name] = ColumnClassification(
            name=cls_schema.name,
            dtype_pandas=cls_schema.dtype_pandas,
            inferred_type=cls_schema.inferred_type,
            confidence=cls_schema.confidence,
            reasons=cls_schema.reasons,
            cardinality=cls_schema.cardinality,
            cardinality_ratio=cls_schema.cardinality_ratio
        )

    val_res = validate_chart_config(
        df=df,
        chart_type=body.chart_type,
        mapping=body.mapping,
        classifications=cls_dataclasses
    )

    validation_schema = ChartValidationResultSchema(
        is_valid=val_res.is_valid,
        errors=val_res.errors,
        warnings=val_res.warnings,
        suggestion=val_res.suggestion
    )

    chart_options = None
    if val_res.is_valid:
        chart_options = build_echarts_for_config(
            df=df,
            chart_type=body.chart_type,
            mapping=body.mapping,
            classifications=cls_dataclasses
        )

    return ChartExploreResponse(
        chart_type=body.chart_type,
        validation=validation_schema,
        chart_options=chart_options
    )

@app.post("/api/query", response_model=ChatMessageResponse)
def query_dataset(
    body: ChatMessageRequest,
    x_session_id: Optional[str] = Header(None)
):
    session, _ = session_manager.get_or_create_session(x_session_id)

    if not body.question or not body.question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")

    return process_chat_query(
        session=session,
        question=body.question.strip(),
        provider=body.provider
    )
