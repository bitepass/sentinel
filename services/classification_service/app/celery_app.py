from celery import Celery
import os
import time
import logging
from dotenv import load_dotenv
from redis import Redis, ConnectionError, TimeoutError

# Configurar logging
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

def wait_for_redis(max_retries: int = 10, retry_delay: float = 2.0) -> bool:
    """
    Espera a que Redis esté disponible antes de continuar.
    Retorna True si Redis está disponible, False si falló después de todos los reintentos.
    """
    logger.info(f"Verificando conectividad con Redis en {REDIS_HOST}:{REDIS_PORT}")
    
    for attempt in range(max_retries):
        try:
            redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, socket_timeout=5)
            redis_client.ping()
            redis_client.close()
            logger.info("✅ Redis está disponible")
            return True
            
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Intento {attempt + 1}/{max_retries}: Redis no disponible: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Esperando {retry_delay} segundos antes del reintento...")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Backoff exponencial
            else:
                logger.error(f"❌ Redis no disponible después de {max_retries} intentos")
                return False
    
    return False

# Verificar Redis antes de configurar Celery
if not wait_for_redis():
    logger.error("No se puede conectar a Redis. El servicio puede no funcionar correctamente.")

# Configuración de Celery
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Crear instancia de Celery
celery_app = Celery(
    "classification_service",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

# Configuración de Celery
celery_app.conf.update(
    # Configuración de tareas
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Configuración de workers
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Configuración de resultados
    result_expires=3600,  # 1 hora
    
    # Configuración de reintentos
    task_acks_late=True,
    worker_disable_rate_limits=False,
    
    # Configuración de colas
    task_default_queue="classification",
    task_routes={
        "app.tasks.classify_document_task": {"queue": "classification"},
    },
    
    # Configuración de monitoreo
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Configuración de timeouts
    task_soft_time_limit=300,  # 5 minutos
    task_time_limit=600,       # 10 minutos
    
    # Configuración robusta de Redis
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_transport_options={
        'socket_connect_timeout': 10,
        'socket_timeout': 30,
        'retry_on_timeout': True,
        'max_connections': 20,
    },
    
    # Configuración de resultados robusta
    result_backend_transport_options={
        'socket_connect_timeout': 10,
        'socket_timeout': 30,
        'retry_on_timeout': True,
        'max_connections': 20,
    }
)

# Configuración de logging
celery_app.conf.update(
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"
)

if __name__ == "__main__":
    celery_app.start()
