# Especificaciones: Servicio de Persistencia

- **Responsabilidad:** Único punto de contacto para leer y escribir datos.
- **Tecnología:** Python, FastAPI.
- **API Contract:**
  - `POST /sheet/prepare`: Recibe una ruta de archivo. Lee el `.xlsx`, valida las columnas A-Q y guarda los datos en una tabla `raw_incidents` en PostgreSQL. Devuelve un `document_id`.
  - `GET /data/chunk/{document_id}`: Devuelve un lote de datos no clasificados para un `document_id`.
  - `POST /data/save_classified_chunk`: Recibe un lote de datos clasificados y los guarda en la tabla `classified_incidents`.
  - `POST /sheet/generate_final/{document_id}`: Toma todos los datos clasificados de un `document_id`, genera un archivo Excel "DELEGACION" con las columnas R-AB en color `#b2a1c7` y con filtros.