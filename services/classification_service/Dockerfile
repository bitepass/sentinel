FROM python:3.11-slim

# Crear usuario no-root para seguridad
RUN groupadd -r sentinel && useradd -r -g sentinel sentinel

WORKDIR /app

# Instalar dependencias del sistema incluyendo curl
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar requirements e instalar dependencias Python
COPY services/classification_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del servicio
COPY services/classification_service /app

# Cambiar ownership al usuario no-root
RUN chown -R sentinel:sentinel /app

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Exponer puerto
EXPOSE 8002

# Cambiar a usuario no-root
USER sentinel

# Comando por defecto (FastAPI)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--proxy-headers"]
