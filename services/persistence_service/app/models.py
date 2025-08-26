from typing import List, Optional

from pydantic import BaseModel, Field


class PrepareRequest(BaseModel):
    file_path: str = Field(..., description="Ruta absoluta del archivo Excel a procesar")


class PrepareResponse(BaseModel):
    document_id: str
    rows_imported: int


class RawIncidentItem(BaseModel):
    id: int
    row_index: int
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


class ChunkResponse(BaseModel):
    document_id: str
    items: List[RawIncidentItem]


class SaveClassifiedItem(BaseModel):
    raw_incident_id: int
    col_r: Optional[str] = None
    col_s: Optional[str] = None
    col_t: Optional[str] = None
    col_u: Optional[str] = None
    col_v: Optional[str] = None
    col_w: Optional[str] = None
    col_x: Optional[str] = None
    col_y: Optional[str] = None
    col_z: Optional[str] = None
    col_aa: Optional[str] = None
    col_ab: Optional[str] = None


class SaveClassifiedChunkRequest(BaseModel):
    document_id: str
    items: List[SaveClassifiedItem]


class SaveClassifiedChunkResponse(BaseModel):
    document_id: str
    saved: int


class GenerateFinalResponse(BaseModel):
    document_id: str
    file_path: str
    rows: int


