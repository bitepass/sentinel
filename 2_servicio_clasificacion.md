# Especificaciones: Servicio de Clasificación

- **Responsabilidad:** Orquestar y ejecutar la clasificación de un documento completo.
- **Tecnología:** Python, FastAPI.
- **API Contract:**
  - `POST /classify/{document_id}`: Inicia el proceso de clasificación.
- **Lógica Interna:**
  1.  Llama al `Servicio de Persistencia` para obtener los lotes de datos del `document_id`.
  2.  Por cada lote, aplica la lógica de clasificación híbrida:
      - **Fase Local:** Usa `config/diccionario_clasificador.json` para clasificar casos obvios.
      - **Fase IA:** Para casos de baja confianza, llama a una API de IA con el contexto de `config/contexto_legal_argentino.txt`.
  3.  **CRÍTICO:** Debe mantener el orden original de las filas.
  4.  Llama al `Servicio de Persistencia` para guardar cada lote clasificado.