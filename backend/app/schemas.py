from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ColumnProfile(BaseModel):
    name: str
    data_type: str
    null_count: int
    null_percentage: float
    unique_count: int
    sample_values: List[Any]
    stats: Optional[Dict[str, Any]] = None

class DatasetProfile(BaseModel):
    filename: str
    file_size_bytes: int
    row_count: int
    column_count: int
    columns: List[ColumnProfile]
    sample_rows: List[Dict[str, Any]]
    table_name: str

class UploadResponse(BaseModel):
    session_id: str
    message: str
    profile: DatasetProfile

class ChatMessageRequest(BaseModel):
    question: str
    provider: Optional[str] = None  # 'groq' or 'gemini'

class EChartsSeries(BaseModel):
    name: str
    type: str  # 'bar', 'line', 'pie', 'scatter'
    data: List[Any]

class EChartsOption(BaseModel):
    title: Optional[Dict[str, Any]] = None
    tooltip: Optional[Dict[str, Any]] = None
    legend: Optional[Dict[str, Any]] = None
    xAxis: Optional[Dict[str, Any]] = None
    yAxis: Optional[Dict[str, Any]] = None
    series: Optional[List[Dict[str, Any]]] = None

class ChatMessageResponse(BaseModel):
    question: str
    sql: str
    explanation: str
    results: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    chart_recommended: bool
    chart_type: Optional[str] = None  # 'bar', 'line', 'pie', 'scatter', 'table'
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
