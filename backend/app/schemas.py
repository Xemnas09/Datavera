from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ColumnClassificationSchema(BaseModel):
    name: str
    dtype_pandas: str
    inferred_type: str  # "numeric" | "categorical" | "identifier" | "datetime"
    confidence: float
    reasons: List[str] = Field(default_factory=list)
    cardinality: int = 0
    cardinality_ratio: float = 0.0

class ColumnProfile(BaseModel):
    name: str
    data_type: str
    null_count: int
    null_percentage: float
    unique_count: int
    sample_values: List[Any]
    stats: Optional[Dict[str, Any]] = None
    classification: Optional[ColumnClassificationSchema] = None

class DatasetProfile(BaseModel):
    filename: str
    file_size_bytes: int
    row_count: int
    column_count: int
    columns: List[ColumnProfile]
    sample_rows: List[Dict[str, Any]]
    table_name: str
    classifications: Optional[Dict[str, ColumnClassificationSchema]] = None

class ReclassifyColumnRequest(BaseModel):
    column_name: str
    target_type: str  # "numeric" | "categorical" | "identifier" | "datetime"

class ChartValidationResultSchema(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestion: Optional[str] = None

class ChartExploreRequest(BaseModel):
    chart_type: str
    mapping: Dict[str, str]  # e.g. {"x": "category", "y": "sales"}

class ChartExploreResponse(BaseModel):
    chart_type: str
    validation: ChartValidationResultSchema
    chart_options: Optional[Dict[str, Any]] = None

class UploadResponse(BaseModel):
    session_id: str
    message: str
    profile: DatasetProfile
    confidence_score: float = 1.0
    requires_user_action: bool = False
    detected_header_index: int = 0
    selected_sheet: Optional[str] = None
    available_sheets: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    raw_preview_rows: List[List[Any]] = Field(default_factory=list)

class IngestionConfigRequest(BaseModel):
    sheet_name: Optional[str] = None
    header_index: Optional[int] = None
    delimiter: Optional[str] = None

class ChatMessageRequest(BaseModel):
    question: str
    provider: Optional[str] = None

class ChatMessageResponse(BaseModel):
    question: str
    sql: str
    explanation: str
    results: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    chart_recommended: bool
    chart_type: Optional[str] = None
    chart_options: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SampleDatasetInfo(BaseModel):
    id: str
    title: str
    description: str
    filename: str
    row_count: int
    column_count: int

class SessionInfoResponse(BaseModel):
    session_id: str
    created_at: str
    last_activity: str
    has_dataset: bool
    dataset_name: Optional[str] = None
    row_count: Optional[int] = None
