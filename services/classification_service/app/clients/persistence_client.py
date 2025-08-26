import httpx
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Dict, Any, Optional
import logging
from ..models import ChunkResponse, SaveClassifiedChunkRequest

logger = logging.getLogger(__name__)

class PersistenceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
    
    # Métodos asíncronos (para FastAPI)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
    async def health(self):
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self.base_url}/health")
            r.raise_for_status()
            return r.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
    async def get_chunk(self, document_id: str, size: int = 200) -> ChunkResponse:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(f"{self.base_url}/data/chunk/{document_id}", params={"size": size})
            r.raise_for_status()
            # Validar respuesta con Pydantic
            raw_data = r.json()
            return ChunkResponse(**raw_data)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
    async def save_classified_chunk(self, payload: SaveClassifiedChunkRequest):
        async with httpx.AsyncClient(timeout=60) as client:
            # Validar payload con Pydantic antes de enviar
            validated_payload = payload.dict()
            r = await client.post(f"{self.base_url}/data/save_classified_chunk", json=validated_payload)
            r.raise_for_status()
            return r.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
    async def generate_final(self, document_id: str):
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{self.base_url}/sheet/generate_final/{document_id}")
            r.raise_for_status()
            return r.json()
    
    # Métodos síncronos (para Celery workers)
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
    def health_sync(self):
        try:
            r = requests.get(f"{self.base_url}/health", timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"Error en health check síncrono: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
    def get_chunk_sync(self, document_id: str, size: int = 200) -> ChunkResponse:
        try:
            r = requests.get(f"{self.base_url}/data/chunk/{document_id}", params={"size": size}, timeout=60)
            r.raise_for_status()
            # Validar respuesta con Pydantic
            raw_data = r.json()
            return ChunkResponse(**raw_data)
        except Exception as e:
            logger.error(f"Error obteniendo chunk síncrono: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
    def save_classified_chunk_sync(self, payload: SaveClassifiedChunkRequest):
        try:
            # Validar payload con Pydantic antes de enviar
            validated_payload = payload.dict()
            r = requests.post(f"{self.base_url}/data/save_classified_chunk", json=payload, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"Error guardando chunk clasificado síncrono: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, max=4))
    def generate_final_sync(self, document_id: str):
        try:
            r = requests.post(f"{self.base_url}/sheet/generate_final/{document_id}", timeout=120)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"Error generando archivo final síncrono: {e}")
            raise
