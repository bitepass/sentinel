FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# DATABASE_URL debe proveerse en runtime, p.ej.:
# postgres://user:pass@host:5432/dbname
ENV DATABASE_URL="sqlite:///./persistence.db"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


