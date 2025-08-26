# Comandos para Ejecutar el Sistema Asíncrono

## 1. Variables de Entorno
Crear archivo `.env` en la raíz del proyecto:
```bash
# Puertos y URLs
PERSISTENCE_HOST=0.0.0.0
PERSISTENCE_PORT=8001
CLASSIFICATION_HOST=0.0.0.0
CLASSIFICATION_PORT=8002
N8N_PORT=5678

# Redis (Broker para Celery)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Persistencia (DEV con SQLite por defecto; en PROD usar Postgres)
DATABASE_URL=sqlite:///./data/persistence.db

# Autenticación API
API_TOKEN=your_secure_token_here

# Opcional IA
OPENAI_API_KEY=

# CORS (si quisieras habilitar orígenes específicos)
ALLOWED_ORIGINS=*
```

## 2. Instalar Dependencias
```bash
# Activar entorno virtual
venv\Scripts\activate

# Instalar dependencias del servicio de clasificación
cd services/classification_service
pip install -r requirements.txt

# Volver a la raíz
cd ../..
```

## 3. Ejecutar con Docker Compose (RECOMENDADO)
```bash
# Construir todas las imágenes
docker-compose build

# Ejecutar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f classification_service
docker-compose logs -f classification_worker
docker-compose logs -f redis
```

## 4. Ejecutar Manualmente (Desarrollo)
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Servicio de Persistencia
cd services/persistence_service
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 3: Worker de Celery
cd services/classification_service
python worker.py

# Terminal 4: Servicio de Clasificación (FastAPI)
cd services/classification_service
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Terminal 5: n8n
npx n8n start
```

## 5. Verificar Estado
```bash
# Health checks
curl http://localhost:8001/health
curl http://localhost:8002/health

# Estado de Redis
redis-cli ping

# Estado de Celery
cd services/classification_service
celery -A app.celery_app inspect active
celery -A app.celery_app inspect stats
```

## 6. Monitoreo
- **Flower (Monitoreo de Celery)**: http://localhost:5555
- **n8n**: http://localhost:5678
- **Servicio de Clasificación**: http://localhost:8002/docs
- **Servicio de Persistencia**: http://localhost:8001/docs

## 7. Escalar Workers
```bash
# Escalar a más workers
docker-compose up -d --scale classification_worker=4

# O manualmente
cd services/classification_service
celery -A app.celery_app worker --loglevel=INFO --concurrency=4 --queues=classification
```

## 8. Detener Todo
```bash
# Con Docker Compose
docker-compose down

# Manualmente
# Ctrl+C en cada terminal
redis-cli shutdown
```
