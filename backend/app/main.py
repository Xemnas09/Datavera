import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import MAX_UPLOAD_SIZE_BYTES
from app.session_manager import session_manager, Session
from app.ingestion import ingest_file_to_session
from app.profiling import profile_dataset
from app.samples import get_sample_list, get_sample_filepath
from app.query_engine import process_chat_query
from app.schemas import (
    UploadResponse,
    SampleDatasetInfo,
    SessionInfoResponse,
    ChatMessageRequest,
    ChatMessageResponse
)

app = FastAPI(
    title="Datavera API",
    description="Backend analytique DuckDB et IA pour l'analyse de fichiers de données",
    version="1.0.0"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Next.js frontend / Vercel proxy
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_current_session(x_session_id: Optional[str] = Header(None)) -> Tuple[Session, str]:
    session, created = session_manager.get_or_create_session(x_session_id)
    return session, session.session_id

@app.get("/health")
def health_check():
    return {"status": "ok", "app": "Datavera API"}

@app.get("/api/session", response_model=SessionInfoResponse)
def get_session_info(x_session_id: Optional[str] = Header(None)):
    session, created = session_manager.get_or_create_session(x_session_id)
    conn = session.get_connection()

    # Check if table 'dataset' exists
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
        ingest_file_to_session(session, file_path, filename)
        file_size = file_path.stat().st_size
        profile = profile_dataset(session, file_size)

        return UploadResponse(
            session_id=session.session_id,
            message=f"Jeu de données exemple '{filename}' chargé avec succès.",
            profile=profile
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement de l'échantillon: {str(e)}")

@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    x_session_id: Optional[str] = Header(None)
):
    session, _ = session_manager.get_or_create_session(x_session_id)

    # Validate extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ['.csv', '.tsv', '.xlsx', '.xls']:
        raise HTTPException(
            status_code=400,
            detail=f"Format de fichier non supporté '{file_ext}'. Seuls les fichiers CSV, TSV, XLSX et XLS sont acceptés."
        )

    # Stream to temporary file
    temp_dir = Path("/tmp/datavera_uploads")
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_file_path = temp_dir / f"{session.session_id}_{file.filename}"
    file_size = 0

    try:
        with temp_file_path.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024): # 1MB chunking
                file_size += len(chunk)
                if file_size > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Fichier trop volumineux. La taille maximale autorisée est de 150 Mo."
                    )
                buffer.write(chunk)

        # Ingest file into DuckDB
        ingest_file_to_session(session, temp_file_path, file.filename)

        # Profile dataset
        profile = profile_dataset(session, file_size)

        return UploadResponse(
            session_id=session.session_id,
            message=f"Fichier '{file.filename}' importé et analysé avec succès.",
            profile=profile
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse du fichier: {str(e)}")
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink(missing_ok=True)

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
