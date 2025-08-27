FROM python:3.11-slim

# Crear usuario no-root para seguridad
RUN groupadd -r sentinel && useradd -r -g sentinel sentinel

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copiar requirements.txt desde el contexto de construcción
COPY services/persistence_service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY services/persistence_service/app ./app

# Cambiar ownership al usuario no-root
RUN chown -R sentinel:sentinel /app

EXPOSE 8001

# DATABASE_URL debe proveerse en runtime, p.ej.:
# postgres://user:pass@host:5432/dbname
ENV DATABASE_URL="sqlite:///./persistence.db"

# Cambiar a usuario no-root
USER sentinel

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]


