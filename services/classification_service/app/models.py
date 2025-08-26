from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class StrategyEnum(str, Enum):
    """Estrategias de clasificación válidas"""
    RULES = "rules"
    HYBRID = "hybrid"

class ClassifyOptions(BaseModel):
    """Opciones de configuración para clasificación"""
    batch_size: int = Field(
        default=200, 
        ge=1, 
        le=2000,
        description="Número de filas por lote (1-2000)"
    )
    max_batches: Optional[int] = Field(
        default=None, 
        ge=1, 
        le=1000,
        description="Número máximo de lotes a procesar"
    )
    strategy: StrategyEnum = Field(
        default=StrategyEnum.RULES,
        description="Estrategia de clasificación: rules o hybrid"
    )
    generate_final: bool = Field(
        default=False,
        description="Si generar archivo Excel final"
    )
    
    @validator('max_batches')
    def validate_max_batches(cls, v, values):
        if v is not None and 'batch_size' in values:
            total_rows = v * values['batch_size']
            if total_rows > 100000:
                raise ValueError(f"Total de filas ({total_rows}) excede el límite de 100,000")
        return v

class RawIncidentData(BaseModel):
    """Datos de incidente sin clasificar del Servicio de Persistencia"""
    id: int
    document_id: str = Field(..., min_length=1, max_length=64)
    row_index: int = Field(..., ge=0)
    source_path: Optional[str] = None
    col_a: Optional[str] = None
    col_b: Optional[str] = None
    col_c: Optional[str] = None
    col_d: Optional[str] = None
    col_e: Optional[str] = None
    col_f: Optional[str] = None
    col_g: Optional[str] = None
    col_h: Optional[str] = None
    col_i: Optional[str] = None
    col_j: Optional[str] = None
    col_k: Optional[str] = None
    col_l: Optional[str] = None
    col_m: Optional[str] = None
    col_n: Optional[str] = None
    col_o: Optional[str] = None
    col_p: Optional[str] = None
    col_q: Optional[str] = None
    created_at: Optional[str] = None

class ChunkResponse(BaseModel):
    """Respuesta de chunk de datos del Servicio de Persistencia"""
    chunk_id: Optional[str] = None
    rows: List[RawIncidentData] = Field(default_factory=list)
    total_available: Optional[int] = None
    has_more: bool = True

class ClassifiedRow(BaseModel):
    """Fila clasificada con validaciones estrictas"""
    row_id: int = Field(..., ge=0)
    raw_incident_id: int = Field(..., ge=1)
    categoria: Optional[str] = Field(None, max_length=100)
    subtipo: Optional[str] = Field(None, max_length=100)
    observaciones: Optional[str] = Field(None, max_length=500)
    
    @validator('categoria', 'subtipo')
    def validate_classification_fields(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v

class SaveClassifiedChunkRequest(BaseModel):
    """Request para guardar chunk clasificado"""
    document_id: str = Field(..., min_length=1, max_length=64)
    rows: List[ClassifiedRow] = Field(..., min_items=1, max_items=1000)

class ClassifyResponse(BaseModel):
    """Respuesta del endpoint de clasificación"""
    document_id: str = Field(..., min_length=1, max_length=64)
    task_id: str = Field(..., min_length=1)
    status: str = Field(..., regex="^(enqueued|processing|completed|failed)$")
    message: str = Field(..., min_length=1, max_length=500)
    strategy: StrategyEnum
    options: Dict[str, Any] = Field(default_factory=dict)

class TaskStatus(BaseModel):
    """Estado de una tarea de Celery"""
    task_id: str = Field(..., min_length=1)
    status: str = Field(..., regex="^(processing|completed|failed)$")
    progress: Optional[int] = Field(None, ge=0, le=100)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class DocumentProgress(BaseModel):
    """Progreso de clasificación de un documento"""
    document_id: str = Field(..., min_length=1, max_length=64)
    active_tasks: int = Field(..., ge=0)
    tasks: List[Dict[str, Any]] = Field(default_factory=list)

class HealthResponse(BaseModel):
    """Respuesta del health check"""
    status: str = Field(..., regex="^(ok|error)$")
    service: str = Field(..., min_length=1)
    redis: Optional[str] = Field(None, regex="^(ok|error)$")
    persistence: Optional[str] = Field(None, regex="^(ok|error)$")
    version: str = Field(..., min_length=1)
    error: Optional[str] = None
