from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import time
import uuid
from datetime import datetime
import re
from dotenv import load_dotenv
from .models import ClassifyOptions, ClassifyResponse, HealthResponse
from .celery_app import celery_app
from .tasks import classify_document_task
import logging

# Configurar logging con formato de auditoría de seguridad
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [SECURITY_AUDIT] - %(message)s'
)
logger = logging.getLogger(__name__)

# Filtro para correlation IDs
class CorrelationFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.correlation_id = "unknown"
    
    def filter(self, record):
        record.correlation_id = getattr(self, 'correlation_id', 'unknown')
        return True

correlation_filter = CorrelationFilter()
logger.addFilter(correlation_filter)

# Cargar variables de entorno
load_dotenv()

# =============================================================================
# CONFIGURACIÓN DE SEGURIDAD - VALIDACIÓN OBLIGATORIA
# =============================================================================

def validate_environment_security():
    """Valida que todas las variables de entorno de seguridad estén configuradas"""
    required_vars = {
        "API_TOKEN": {
            "value": os.getenv("API_TOKEN"),
            "min_length": 32,
            "description": "Token de autenticación API"
        },
        "REDIS_PASSWORD": {
            "value": os.getenv("REDIS_PASSWORD"),
            "min_length": 16,
            "description": "Contraseña de Redis"
        },
        "FLOWER_USER": {
            "value": os.getenv("FLOWER_USER"),
            "min_length": 3,
            "description": "Usuario de Flower"
        },
        "FLOWER_PASSWORD": {
            "value": os.getenv("FLOWER_PASSWORD"),
            "min_length": 16,
            "description": "Contraseña de Flower"
        },
        "N8N_USER": {
            "value": os.getenv("N8N_USER"),
            "min_length": 3,
            "description": "Usuario de n8n"
        },
        "N8N_PASSWORD": {
            "value": os.getenv("N8N_PASSWORD"),
            "min_length": 16,
            "description": "Contraseña de n8n"
        },
        "N8N_SESSION_SECRET": {
            "value": os.getenv("N8N_SESSION_SECRET"),
            "min_length": 32,
            "description": "Secreto de sesión de n8n"
        }
    }
    
    missing_vars = []
    weak_vars = []
    
    for var_name, config in required_vars.items():
        if not config["value"]:
            missing_vars.append(f"{var_name}: {config['description']}")
        elif len(config["value"]) < config["min_length"]:
            weak_vars.append(f"{var_name}: mínimo {config['min_length']} caracteres")
    
    if missing_vars:
        raise RuntimeError(f"Variables de entorno de seguridad faltantes: {', '.join(missing_vars)}")
    
    if weak_vars:
        raise RuntimeError(f"Variables de entorno de seguridad débiles: {', '.join(weak_vars)}")
    
    logger.info("✅ Todas las variables de entorno de seguridad están configuradas correctamente")

# Validar entorno de seguridad al iniciar
validate_environment_security()

# Configuración de autenticación - OBLIGATORIA
API_TOKEN = os.getenv("API_TOKEN")

# Configuración de rate limiting
PUBLIC_RATE_LIMIT = os.getenv("PUBLIC_RATE_LIMIT", "30")
AUTHENTICATED_RATE_LIMIT = os.getenv("AUTHENTICATED_RATE_LIMIT", "100")

# Configuración de logging de auditoría
SECURITY_AUDIT_LOGGING = os.getenv("SECURITY_AUDIT_LOGGING", "true").lower() == "true"

security = HTTPBearer(auto_error=True)

def log_security_event(event_type: str, details: dict, client_ip: str = None):
    """Log de eventos de seguridad para auditoría"""
    if SECURITY_AUDIT_LOGGING:
        audit_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        logger.warning(
            f"[SECURITY_AUDIT] {audit_id} | {event_type} | {timestamp} | "
            f"IP: {client_ip or 'unknown'} | Details: {details}"
        )

def verify_api_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifica el token API del header Authorization.
    Rechaza la petición si el token no coincide.
    """
    client_ip = get_client_ip()
    
    if credentials.credentials != API_TOKEN:
        # Log de intento de autenticación fallido
        log_security_event(
            "AUTH_FAILED",
            {
                "token_length": len(credentials.credentials),
                "token_prefix": credentials.credentials[:4] + "..." if len(credentials.credentials) > 4 else "short",
                "user_agent": "unknown"
            },
            client_ip
        )
        
        raise HTTPException(
            status_code=401,
            detail="Token de autenticación inválido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Log de autenticación exitosa
    log_security_event(
        "AUTH_SUCCESS",
        {
            "token_length": len(credentials.credentials),
            "timestamp": datetime.utcnow().isoformat()
        },
        client_ip
    )
    
    return True

def get_client_ip():
    """Obtiene IP del cliente de forma segura"""
    # En producción, implementar validación de X-Forwarded-For
    return "unknown"  # Placeholder para implementación completa

def sanitize_document_id(document_id: str) -> str:
    """Sanitiza y valida el ID del documento"""
    if not document_id or len(document_id) > MAX_DOCUMENT_ID_LENGTH:
        raise HTTPException(status_code=400, detail="ID de documento inválido")
    
    # Solo permitir caracteres alfanuméricos, guiones y guiones bajos
    if not re.match(r'^[a-zA-Z0-9_-]+$', document_id):
        raise HTTPException(status_code=400, detail="ID de documento contiene caracteres inválidos")
    
    return document_id.strip()

def validate_request_size(request: Request):
    """Valida el tamaño del request"""
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_SIZE:
        raise HTTPException(status_code=413, detail="Request demasiado grande")

def validate_input_security(document_id: str, options: ClassifyOptions):
    """Validación de seguridad para inputs"""
    security_issues = []
    
    # Validar document_id
    if not document_id or len(document_id) > 100:
        security_issues.append("document_id inválido o demasiado largo")
    
    # Validar batch_size
    if options.batch_size < 1 or options.batch_size > 1000:
        security_issues.append("batch_size fuera de rango permitido")
    
    # Validar max_batches
    if options.max_batches < 1 or options.max_batches > 100:
        security_issues.append("max_batches fuera de rango permitido")
    
    # Validar strategy
    allowed_strategies = ["sequential", "parallel", "hybrid"]
    if options.strategy not in allowed_strategies:
        security_issues.append(f"strategy no permitida: {options.strategy}")
    
    if security_issues:
        log_security_event(
            "INPUT_VALIDATION_FAILED",
            {
                "document_id": document_id,
                "options": options.dict(),
                "issues": security_issues
            }
        )
        raise HTTPException(
            status_code=400,
            detail=f"Validación de entrada fallida: {'; '.join(security_issues)}"
        )

# Configurar rate limiting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Servicio de Clasificación Asíncrono", 
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENABLE_DOCS", "false").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("ENABLE_DOCS", "false").lower() == "true" else None
)

# Agregar rate limiter a la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# =============================================================================
# MIDDLEWARE DE SEGURIDAD
# =============================================================================

# Middleware de hosts confiables
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # En producción, especificar solo dominios permitidos
)

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

# =============================================================================
# MIDDLEWARE DE AUDITORÍA DE SEGURIDAD
# =============================================================================

@app.middleware("http")
async def security_audit_middleware(request: Request, call_next):
    """Middleware para auditoría de seguridad de todas las requests"""
    start_time = time.time()
    client_ip = get_client_ip()
    request_id = str(uuid.uuid4())
    
    # Configurar correlation ID
    request.state.correlation_id = request_id
    correlation_filter.correlation_id = request_id
    
    # Log de inicio de request
    log_security_event(
        "REQUEST_START",
        {
            "request_id": request_id,
            "correlation_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": client_ip
        }
    )
    
    try:
        response = await call_next(request)
        
        # Agregar correlation ID al header de respuesta
        response.headers["X-Correlation-ID"] = request_id
        
        # Log de request exitosa
        log_security_event(
            "REQUEST_SUCCESS",
            {
                "request_id": request_id,
                "correlation_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round((time.time() - start_time) * 1000, 2)
            }
        )
        
        return response
        
    except Exception as e:
        # Log de error en request
        log_security_event(
            "REQUEST_ERROR",
            {
                "request_id": request_id,
                "correlation_id": request_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "duration_ms": round((time.time() - start_time) * 1000, 2)
            }
        )
        raise

# Configuración de límites de seguridad
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB máximo
MAX_DOCUMENT_ID_LENGTH = 100

# Configuración del servicio de persistencia
PERSISTENCE_HOST = os.getenv("PERSISTENCE_HOST", "localhost")
PERSISTENCE_PORT = os.getenv("PERSISTENCE_PORT", "8001")
PERSISTENCE_URL = f"http://{PERSISTENCE_HOST}:{PERSISTENCE_PORT}"

@app.on_event("startup")
async def startup_event():
    logger.info("Servicio de clasificación asíncrono iniciado")
    logger.info(f"URL del servicio de persistencia: {PERSISTENCE_URL}")

@app.get("/health", response_model=HealthResponse)
@limiter.limit("30/minute")  # Rate limiting agresivo para endpoints públicos
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
@limiter.limit("10/minute")  # Rate limiting extremo para operaciones pesadas
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
    # Validaciones de seguridad
    validate_request_size(request)
    document_id = sanitize_document_id(document_id)
    validate_input_security(document_id, options)
    
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
    # Validaciones de seguridad
    validate_request_size(request)
    if not re.match(r'^[a-zA-Z0-9_-]+$', task_id):
        raise HTTPException(status_code=400, detail="ID de tarea inválido")
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
    # Validaciones de seguridad
    validate_request_size(request)
    document_id = sanitize_document_id(document_id)
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
