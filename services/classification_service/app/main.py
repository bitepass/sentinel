from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv
from .models import ClassifyOptions, ClassifyResponse, HealthResponse
from .celery_app import celery_app
from .tasks import classify_document_task
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de autenticación
API_TOKEN = os.getenv("API_TOKEN", "default_token_change_in_production")
security = HTTPBearer()

def verify_api_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica el token API del header Authorization.
    Rechaza la petición si el token no coincide.
    """
    if not API_TOKEN:
        logger.warning("API_TOKEN no configurado - autenticación deshabilitada")
        return True
    
    if credentials.credentials != API_TOKEN:
        logger.warning(f"Token API inválido: {credentials.credentials[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Token de autenticación inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return True

# Configurar rate limiting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="Servicio de Clasificación Asíncrono", version="2.0.0")

# Agregar rate limiter a la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS - Solo orígenes específicos por seguridad
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5678,http://127.0.0.1:5678").split(",")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Solo orígenes específicos, no wildcard "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Solo métodos necesarios
    allow_headers=["*"],
)

# Configuración del servicio de persistencia
PERSISTENCE_HOST = os.getenv("PERSISTENCE_HOST", "localhost")
PERSISTENCE_PORT = os.getenv("PERSISTENCE_PORT", "8001")
PERSISTENCE_URL = f"http://{PERSISTENCE_HOST}:{PERSISTENCE_PORT}"

@app.on_event("startup")
async def startup_event():
    logger.info("Servicio de clasificación asíncrono iniciado")
    logger.info(f"URL del servicio de persistencia: {PERSISTENCE_URL}")

@app.get("/health", response_model=HealthResponse)
@limiter.limit("100/minute")  # 100 requests por minuto por IP
async def health_check(request: Request):
    """Verificar estado del servicio y dependencias"""
    try:
        # Verificar Redis
        redis_info = celery_app.control.inspect().stats()
        redis_status = "ok" if redis_info else "error"
        
        # Verificar servicio de persistencia
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{PERSISTENCE_URL}/health")
            persistence_status = "ok" if response.status_code == 200 else "error"
        
        return HealthResponse(
            status="ok",
            service="classification_service",
            redis=redis_status,
            persistence=persistence_status,
            version="2.0.0"
        )
    except Exception as e:
        logger.error(f"Error en health check: {e}")
        return HealthResponse(
            status="error",
            service="classification_service",
            error=str(e)
        )

@app.post("/classify/{document_id}", response_model=ClassifyResponse)
@limiter.limit("50/minute")  # 50 requests por minuto por IP (más restrictivo para operaciones pesadas)
async def classify_document(
    request: Request,
    document_id: str,
    options: ClassifyOptions,
    background_tasks: BackgroundTasks,
    token_verified: bool = Depends(verify_api_token)
):
    """
    Inicia el proceso de clasificación asíncrono.
    Responde inmediatamente con un task_id para seguimiento.
    """
    try:
        # Encolar tarea de clasificación
        task = classify_document_task.delay(
            document_id=document_id,
            batch_size=options.batch_size,
            max_batches=options.max_batches,
            strategy=options.strategy,
            generate_final=options.generate_final
        )
        
        logger.info(f"Tarea de clasificación encolada: {task.id} para documento {document_id}")
        
        return ClassifyResponse(
            document_id=document_id,
            task_id=task.id,
            status="enqueued",
            message="Tarea de clasificación encolada exitosamente",
            strategy=options.strategy,
            options=options.dict()
        )
        
    except Exception as e:
        logger.error(f"Error al encolar tarea de clasificación: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/task/{task_id}/status")
@limiter.limit("100/minute")  # 100 requests por minuto por IP
async def get_task_status(
    request: Request,
    task_id: str,
    token_verified: bool = Depends(verify_api_token)
):
    """
    Obtener el estado de una tarea de clasificación
    """
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.ready():
            if task_result.successful():
                result = task_result.result
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "result": result
                }
            else:
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(task_result.result)
                }
        else:
            return {
                "task_id": task_id,
                "status": "processing",
                "progress": task_result.info.get("progress", 0) if task_result.info else 0
            }
            
    except Exception as e:
        logger.error(f"Error al obtener estado de tarea {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/document/{document_id}/progress")
@limiter.limit("100/minute")  # 100 requests por minuto por IP
async def get_document_progress(
    request: Request,
    document_id: str,
    token_verified: bool = Depends(verify_api_token)
):
    """
    Obtener el progreso general de clasificación de un documento
    """
    try:
        # Buscar tareas activas para este documento
        active_tasks = celery_app.control.inspect().active()
        
        document_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                if task.get("args") and document_id in str(task["args"]):
                    document_tasks.append({
                        "task_id": task["id"],
                        "worker": worker,
                        "started": task.get("time_start", 0)
                    })
        
        return {
            "document_id": document_id,
            "active_tasks": len(document_tasks),
            "tasks": document_tasks
        }
        
    except Exception as e:
        logger.error(f"Error al obtener progreso del documento {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
