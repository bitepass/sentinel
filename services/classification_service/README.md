# Servicio de Clasificación - Proyecto Sentinel

Microservicio responsable de la clasificación automática de incidentes delictivos usando lógica híbrida.

## Características

- **Clasificación Híbrida**: Combina reglas locales con IA (futuro)
- **Procesamiento por Chunks**: Maneja grandes volúmenes de datos eficientemente
- **Comunicación Asíncrona**: Se comunica con el servicio de persistencia
- **Background Processing**: Las clasificaciones se ejecutan en background

## Estructura del Proyecto

```
services/classification_service/
├─ app/
│  ├─ __init__.py
│  ├─ main.py              # FastAPI app principal
│  ├─ classifier.py         # Lógica de clasificación
│  ├─ models.py             # Modelos Pydantic
│  └─ clients/
│     ├─ __init__.py
│     └─ persistence_client.py  # Cliente HTTP para persistencia
├─ requirements.txt
├─ Dockerfile
└─ README.md
```

## Endpoints

### `GET /health`
Verifica el estado del servicio y su conexión con persistencia.

### `POST /classify/{document_id}`
Inicia la clasificación de un documento con opciones configurables:
- `batch_size`: Tamaño de cada lote (default: 200)
- `max_batches`: Máximo número de lotes (default: sin límite)
- `strategy`: "rules" (solo reglas) o "hybrid" (reglas + IA)
- `generate_final`: Si generar archivo final al completar

## Configuración

### Variables de Entorno

- `PERSISTENCE_URL`: URL del servicio de persistencia (default: http://localhost:8001)
- `OPENAI_API_KEY`: API key para clasificación por IA (opcional)
- `HOST`: Host de binding (default: 0.0.0.0)
- `PORT`: Puerto del servicio (default: 8002)

### Archivos de Configuración

El servicio busca en `../../config/` (desde la raíz del repo):
- `diccionario_policial.json`: Reglas de clasificación local
- `criterios.txt`: Criterios de clasificación
- `contexto_legal_argentino.txt`: Contexto para clasificación por IA

## Uso

### Desarrollo Local

```bash
cd services/classification_service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Docker

```bash
cd services/classification_service
docker build -t classification-service .
docker run -p 8002:8002 -e PERSISTENCE_URL=http://host.docker.internal:8001 classification-service
```

### Ejemplo de Uso

```bash
# Iniciar clasificación con opciones por defecto
curl -X POST "http://localhost:8002/classify/123e4567-e89b-12d3-a456-426614174000" \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 200, "strategy": "rules", "generate_final": false}'

# Clasificación híbrida con límite de lotes
curl -X POST "http://localhost:8002/classify/123e4567-e89b-12d3-a456-426614174000" \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 100, "max_batches": 10, "strategy": "hybrid", "generate_final": true}'

# Health check
curl "http://localhost:8002/health"
```

## Flujo de Clasificación

1. **Recepción**: Se recibe solicitud de clasificación con opciones configurables
2. **Procesamiento**: La clasificación se ejecuta de forma síncrona
3. **Chunks**: Se obtienen datos del servicio de persistencia en lotes configurables
4. **Clasificación**: Se aplica estrategia seleccionada (rules/hybrid)
5. **Persistencia**: Se guardan los resultados clasificados
6. **Control de Lotes**: Se respeta `max_batches` si está configurado
7. **Archivo Final**: Opcionalmente se genera Excel final
8. **Completado**: Proceso finaliza con estadísticas detalladas

## Integración con n8N

El servicio está diseñado para integrarse con n8N:

1. **Trigger**: n8N llama a `POST /classify/{document_id}` con opciones de configuración
2. **Procesamiento**: La clasificación se ejecuta de forma síncrona con control de lotes
3. **Opciones**: n8N puede configurar `batch_size`, `max_batches`, `strategy` y `generate_final`
4. **Respuesta**: Se recibe confirmación inmediata con estadísticas del proceso
5. **Archivo Final**: Si `generate_final=true`, se genera automáticamente el Excel final

## Logs

El servicio registra todas las operaciones importantes:
- Inicio de clasificaciones
- Procesamiento de chunks
- Errores y excepciones
- Comunicación con persistencia

## Monitoreo

- **Health Check**: Verifica estado del servicio y dependencias
- **Logs**: Información detallada de operaciones
- **Métricas**: En futuras versiones se pueden agregar métricas de rendimiento
