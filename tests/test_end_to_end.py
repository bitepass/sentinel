# tests/test_end_to_end.py
import os
import pytest
from fastapi.testclient import TestClient
from main import app  # Tu FastAPI app
from database import get_db, Base, engine, SessionLocal
from sqlalchemy.orm import Session
import pandas as pd

# -----------------------
# Configuración del DB de prueba
# -----------------------
@pytest.fixture(scope="module")
def test_db():
    # Crea todas las tablas
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

# -----------------------
# Cliente de prueba
# -----------------------
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

# -----------------------
# Test End-to-End
# -----------------------
def test_end_to_end(client: TestClient, test_db: Session):
    # 1️⃣ Subir Excel de prueba
    file_path = "pruebas/SAN_MARTIN_2025.xlsx"
    with open(file_path, "rb") as f:
        response = client.post("/upload_excel/", files={"file": f})
    assert response.status_code == 200
    uploaded_file_id = response.json()["file_id"]

    # 2️⃣ Ejecutar clasificación
    response = client.post(f"/classify_excel/{uploaded_file_id}")
    assert response.status_code == 200
    classified_columns = response.json()["new_columns"]
    # Verificamos que columnas R–AB estén presentes
    expected_cols = [chr(c) for c in range(ord("R"), ord("AB")+1)]
    for col in expected_cols:
        assert col in classified_columns

    # 3️⃣ Generar Excel final
    response = client.get(f"/generate_excel/{uploaded_file_id}")
    assert response.status_code == 200
    output_path = "pruebas/SAN_MARTIN_2025_final.xlsx"
    with open(output_path, "wb") as f:
        f.write(response.content)

    # 4️⃣ Verificar Excel final
    df = pd.read_excel(output_path)
    for col in expected_cols:
        assert col in df.columns

    # 5️⃣ Verificar DB (ejemplo)
    records = test_db.query(YourTable).all()  # Cambiá 'YourTable' por tu tabla
    assert len(records) > 0

    # 6️⃣ Limpieza
    os.remove(output_path)
