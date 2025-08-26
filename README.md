# Crear README.md con codificación correcta
@"
# Sistema de Clasificación de Expedientes Policiales

Sistema asíncrono para clasificación automática de expedientes policiales usando IA híbrida (reglas + ML).

## Características
- 🚀 Procesamiento asíncrono con Celery y Redis
- 🔐 Autenticación por tokens JWT
- ⚡ Rate limiting y protección contra DoS
- ✅ Validación de datos con Pydantic
- 🐳 Dockerizado y escalable

## Instalación
\`\`\`bash
docker-compose up -d
\`\`\`

## Uso
1. Configurar variables en \`.env\`
2. Agregar header \`Authorization: Bearer <token>\` en n8n
3. Ejecutar flujo de clasificación
"@ | Out-File -Encoding UTF8 README.md
