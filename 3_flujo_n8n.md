# Especificaciones: Flujo de n8n (Orquestador)

- **Trigger:** Webhook de Discord. Recibe una URL a una planilla.
- **Pasos:**
  1.  **HTTP Request (Nodo 1):** Llama a `POST /sheet/prepare` en el `Servicio de Persistencia` con la URL. Guarda el `document_id` devuelto.
  2.  **HTTP Request (Nodo 2):** Llama a `POST /classify/{document_id}` en el `Servicio de Clasificación`.
  3.  **HTTP Request (Nodo 3):** Llama a `POST /sheet/generate_final/{document_id}` en el `Servicio de Persistencia`.
  4.  **Discord (Nodo 4):** Envía un mensaje de confirmación con el archivo final.
- **Manejo de Errores:** Cada nodo HTTP Request debe tener 2 reintentos en caso de fallo. Si falla definitivamente, debe enviar una notificación de error a Discord.