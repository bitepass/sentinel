# mock_n8n.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
import shutil
import os

app = FastAPI()
UPLOAD_FOLDER = "mock_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Simula subir archivo
@app.post("/upload_excel/")
async def upload_excel(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # Devuelve un "file_id" simulado
    return {"file_id": file.filename}

# Simula clasificación
@app.post("/classify_excel/{file_id}")
async def classify_excel(file_id: str):
    # Devuelve columnas nuevas simuladas
    new_columns = [chr(c) for c in range(ord("R"), ord("Z")+1)] + ["AA", "AB"]
    return {"file_id": file_id, "new_columns": new_columns}

# Simula generación de Excel final
@app.get("/generate_excel/{file_id}")
async def generate_excel(file_id: str):
    # Simplemente devuelve el archivo subido
    file_path = os.path.join(UPLOAD_FOLDER, file_id)
    if not os.path.exists(file_path):
        return JSONResponse({"error": "Archivo no encontrado"}, status_code=404)
    return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
