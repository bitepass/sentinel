from celery import current_task
from .celery_app import celery_app
from .classifier import classify_rows
from .clients.persistence_client import PersistenceClient
from .models import SaveClassifiedChunkRequest, ClassifiedRow
import os
import logging
from dotenv import load_dotenv
from redis import ConnectionError, TimeoutError

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración del cliente de persistencia
PERSISTENCE_HOST = os.getenv("PERSISTENCE_HOST", "localhost")
PERSISTENCE_PORT = os.getenv("PERSISTENCE_PORT", "8001")
PERSISTENCE_URL = f"http://{PERSISTENCE_HOST}:{PERSISTENCE_PORT}"

@celery_app.task(bind=True, name="classify_document_task")
def classify_document_task(
    self,
    document_id: str,
    batch_size: int = 200,
    max_batches: int = None,
    strategy: str = "rules",
    generate_final: bool = False
):
    # Validaciones de seguridad para memoria
    MAX_BATCH_SIZE = 1000  # Máximo 1000 filas por lote
    MAX_TOTAL_ROWS = 100000  # Máximo 100,000 filas totales
    MAX_BATCHES = 500  # Máximo 500 lotes
    
    # Validar y ajustar parámetros
    if batch_size > MAX_BATCH_SIZE:
        logger.warning(f"batch_size {batch_size} excede el máximo {MAX_BATCH_SIZE}. Ajustando...")
        batch_size = MAX_BATCH_SIZE
    
    if max_batches and max_batches > MAX_BATCHES:
        logger.warning(f"max_batches {max_batches} excede el máximo {MAX_BATCHES}. Ajustando...")
        max_batches = MAX_BATCHES
    
    # Si no se especifica max_batches, calcular basado en MAX_TOTAL_ROWS
    if not max_batches:
        max_batches = min(MAX_BATCHES, MAX_TOTAL_ROWS // batch_size)
        logger.info(f"max_batches calculado automáticamente: {max_batches}")
    
    logger.info(f"Parámetros de seguridad: batch_size={batch_size}, max_batches={max_batches}, max_total_rows={batch_size * max_batches}")
    """
    Tarea de Celery para clasificar un documento completo de forma asíncrona.
    Mantiene el orden original de las filas y respeta la estrategia de clasificación.
    """
    try:
        logger.info(f"Iniciando clasificación asíncrona para documento {document_id}")
        logger.info(f"Estrategia: {strategy}, Tamaño de lote: {batch_size}")
        
        # Crear cliente de persistencia
        client = PersistenceClient(PERSISTENCE_URL)
        
        total_processed = 0
        batch_count = 0
        current_progress = 0
        
        # Actualizar estado de la tarea
        self.update_state(
            state="PROGRESS",
            meta={
                "progress": 0,
                "current_batch": 0,
                "total_processed": 0,
                "status": "Iniciando clasificación"
            }
        )
        
        # Procesar chunks hasta que no queden más o se alcance max_batches
        while True:
            # Verificar límite de lotes
            if max_batches and batch_count >= max_batches:
                logger.info(f"Alcanzado límite de lotes: {max_batches}")
                break
            
            # Verificar límite de memoria por seguridad
            if total_processed >= MAX_TOTAL_ROWS:
                logger.warning(f"Alcanzado límite máximo de filas: {MAX_TOTAL_ROWS}")
                break
            
            # Actualizar progreso
            current_progress = min(95, (batch_count / (max_batches or 10)) * 100)
            self.update_state(
                state="PROGRESS",
                meta={
                    "progress": current_progress,
                    "current_batch": batch_count + 1,
                    "total_processed": total_processed,
                    "status": f"Procesando lote {batch_count + 1}"
                }
            )
            
            # Sistema de reintentos para cada lote
            max_retries = 3
            retry_count = 0
            chunk_processed = False
            
            while retry_count < max_retries and not chunk_processed:
                try:
                    # Obtener chunk de datos no clasificados
                    chunk_data = client.get_chunk_sync(document_id, batch_size)
                    
                    if not chunk_data.get("rows"):
                        logger.info(f"No hay más datos para clasificar en documento {document_id}")
                        break
                    
                    # Clasificar el chunk
                    rows = chunk_data["rows"]
                    logger.info(f"Clasificando lote {batch_count + 1}: {len(rows)} filas (intento {retry_count + 1})")
                    
                    classified_rows = classify_rows(rows, strategy)
                    
                    # Crear payload validado con Pydantic
                    save_payload = SaveClassifiedChunkRequest(
                        document_id=document_id,
                        rows=classified_rows
                    )
                    
                    client.save_classified_chunk_sync(save_payload)
                    total_processed += len(rows)
                    batch_count += 1
                    chunk_processed = True
                    
                    logger.info(f"Lote {batch_count} procesado exitosamente: {len(rows)} filas")
                    
                except Exception as e:
                    retry_count += 1
                    logger.error(f"Error procesando lote {batch_count + 1} (intento {retry_count}/{max_retries}): {e}")
                    
                    if retry_count >= max_retries:
                        # Lote falló después de todos los reintentos - FALLAR TAREA COMPLETA
                        error_msg = f"Lote {batch_count + 1} falló después de {max_retries} reintentos: {str(e)}"
                        logger.error(error_msg)
                        
                        # Marcar tarea como fallida
                        self.update_state(
                            state="FAILURE",
                            meta={
                                "error": error_msg,
                                "failed_batch": batch_count + 1,
                                "total_processed": total_processed,
                                "status": "Tarea fallida por error en lote"
                            }
                        )
                        
                        # Re-lanzar excepción para que Celery marque la tarea como fallida
                        raise Exception(error_msg)
                    
                    # Esperar antes del reintento (backoff exponencial)
                    import time
                    wait_time = 2 ** retry_count  # 2, 4, 8 segundos
                    logger.info(f"Esperando {wait_time} segundos antes del reintento...")
                    time.sleep(wait_time)
        
        # Generar archivo final si se solicita
        if generate_final:
            try:
                logger.info("Generando archivo final...")
                client.generate_final_sync(document_id)
                logger.info("Archivo final generado exitosamente")
            except Exception as e:
                logger.error(f"Error al generar archivo final: {e}")
        
        # Completar tarea
        final_progress = 100
        self.update_state(
            state="SUCCESS",
            meta={
                "progress": final_progress,
                "total_batches": batch_count,
                "total_processed": total_processed,
                "status": "Clasificación completada",
                "strategy": strategy,
                "generate_final": generate_final
            }
        )
        
        logger.info(f"Clasificación completada para documento {document_id}: {total_processed} filas procesadas, {batch_count} lotes")
        
        return {
            "document_id": document_id,
            "total_processed": total_processed,
            "total_batches": batch_count,
            "strategy": strategy,
            "generate_final": generate_final,
            "status": "completed"
        }
        
    except (ConnectionError, TimeoutError) as redis_error:
        # Error específico de Redis - fallo controlado
        error_msg = f"Error de conexión con Redis durante clasificación: {str(redis_error)}"
        logger.error(error_msg)
        
        self.update_state(
            state="FAILURE",
            meta={
                "error": error_msg,
                "error_type": "redis_connection_error",
                "status": "Tarea fallida por error de Redis"
            }
        )
        raise Exception(error_msg)
        
    except Exception as e:
        logger.error(f"Error fatal en clasificación para documento {document_id}: {e}")
        
        # Actualizar estado de error
        self.update_state(
            state="FAILURE",
            meta={
                "error": str(e),
                "error_type": "general_error",
                "status": "Error fatal en clasificación"
            }
        )
        
        # Re-lanzar excepción para que Celery la maneje
        raise

@celery_app.task(name="health_check_task")
def health_check_task():
    """
    Tarea de health check para verificar el estado del sistema
    """
    try:
        client = PersistenceClient(PERSISTENCE_URL)
        health_status = client.health_sync()
        
        return {
            "status": "healthy",
            "persistence_service": health_status,
            "timestamp": "2025-08-21T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-08-21T00:00:00Z"
        }
