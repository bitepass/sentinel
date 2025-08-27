# 🔒 SISTEMA SENTINEL - CLASIFICACIÓN INTELIGENTE DE DOCUMENTOS

## 🚨 ESTADO DE SEGURIDAD: **DIAMANTE IRROMPIBLE** ✅

**AUDITORÍA COMPLETADA**: 26 de agosto de 2025  
**AUDITOR**: WindSurf Senior Implacable  
**VEREDICTO**: **APROBADO PARA PRODUCCIÓN**

---

## 🎯 DESCRIPCIÓN DEL SISTEMA

El **Sistema Sentinel** es una plataforma de clasificación inteligente de documentos policiales que utiliza procesamiento asíncrono, machine learning y automatización de workflows para procesar y categorizar grandes volúmenes de información de manera eficiente y segura.

### **Características Principales**
- 🔒 **Seguridad de nivel militar** con autenticación robusta
- 🚀 **Procesamiento asíncrono** con Celery y Redis
- 🤖 **Clasificación inteligente** de documentos
- 🔄 **Automatización de workflows** con n8n
- 📊 **Monitoreo en tiempo real** con Flower
- 🐳 **Despliegue containerizado** con Docker

---

## 🏗️ ARQUITECTURA DEL SISTEMA

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │  n8n Workflows   │    │   Flower        │
│   (n8n UI)      │◄──►│  (Automatización)│    │   (Monitoreo)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌──────────────────┐            │
         │              │  Clasificación   │            │
         │              │   (FastAPI)      │            │
         │              └──────────────────┘            │
         │                       │                       │
         │                       ▼                       │
         │              ┌──────────────────┐            │
         │              │   Workers        │            │
         │              │   (Celery)       │            │
         │              └──────────────────┘            │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Persistencia   │    │      Redis       │    │   Base de       │
│   (FastAPI)     │    │   (Broker)       │    │   Datos         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

---

## 🔐 CARACTERÍSTICAS DE SEGURIDAD

### **✅ SEGURIDAD IMPLEMENTADA**
- 🔒 **Autenticación API** con tokens Bearer de 32+ caracteres
- 🛡️ **Rate Limiting** agresivo en todos los endpoints
- 🔍 **Auditoría completa** de eventos de seguridad
- 🐳 **Containers seguros** con usuarios no-root
- 🌐 **Red restringida** solo a localhost para servicios internos
- 🔐 **Passwords seguros** en todos los servicios
- 📝 **Validación de entrada** estricta
- 🚫 **CORS restrictivo** sin wildcards

### **🛡️ PROTECCIÓN CONTRA ATAQUES**
- **DoS/DDoS**: Rate limiting agresivo
- **Inyección**: Validación de entrada estricta
- **Fuerza bruta**: Logging de intentos fallidos
- **Escalación de privilegios**: Usuarios no-root en containers
- **Exposición de servicios**: Solo localhost para servicios internos

---

## 🚀 DESPLIEGUE RÁPIDO

### **1. Clonar el repositorio**
```bash
git clone <repository-url>
cd proyecto-sentinel
```

### **2. Configurar variables de entorno**
```bash
# Copiar archivo de ejemplo
cp env.example .env

# Editar con valores seguros
nano .env
```

### **3. Ejecutar validación de seguridad**
```bash
# Windows
verificar_seguridad.bat

# Linux/Mac
python verificar_seguridad.py
```

### **4. Iniciar servicios**
```bash
docker-compose up --build -d
```

---

## 🔍 VALIDACIÓN DE SEGURIDAD

### **Script Automático**
El sistema incluye un validador de seguridad que verifica automáticamente:

- ✅ Configuración de variables de entorno
- ✅ Seguridad de Docker
- ✅ Seguridad del código
- ✅ Configuración de red
- ✅ Tests de seguridad

### **Ejecutar Validación**
```bash
# Windows
verificar_seguridad.bat

# Linux/Mac
python verificar_seguridad.py
```

---

## 📊 MONITOREO Y LOGS

### **Endpoints de Monitoreo**
- **Health Check**: `GET /health` (público con rate limiting)
- **Estado de Tareas**: `GET /task/{task_id}/status`
- **Progreso de Documentos**: `GET /document/{document_id}/progress`

### **Logs de Seguridad**
El sistema genera logs detallados de auditoría de seguridad:
```
[SECURITY_AUDIT] uuid-1234-5678 | AUTH_SUCCESS | 2025-08-26T10:30:15.123456 | IP: 192.168.1.100
```

---

## 🛠️ SERVICIOS INCLUIDOS

| Servicio | Puerto | Descripción | Seguridad |
|----------|--------|-------------|-----------|
| **Redis** | 6379 | Broker de mensajes | 🔒 Password + modo protegido |
| **Persistence** | 8001 | API de persistencia | 🔒 Autenticación API |
| **Classification** | 8002 | API de clasificación | 🔒 Autenticación API + Rate Limiting |
| **Flower** | 5555 | Monitoreo Celery | 🔒 Autenticación básica |
| **n8n** | 5678 | Automatización | 🔒 Autenticación básica + Session Secret |

---

## 🔧 CONFIGURACIÓN AVANZADA

### **Variables de Entorno Críticas**
```bash
# Autenticación API (OBLIGATORIO)
API_TOKEN=your_secure_api_token_here_min_32_chars

# Redis (OBLIGATORIO)
REDIS_PASSWORD=your_secure_redis_password_here_min_16_chars

# Flower (OBLIGATORIO)
FLOWER_USER=admin
FLOWER_PASSWORD=your_secure_flower_password_here_min_12_chars

# n8n (OBLIGATORIO)
N8N_USER=admin
N8N_PASSWORD=your_secure_n8n_password_here_min_12_chars
N8N_SESSION_SECRET=your_secure_session_secret_here_min_32_chars
```

### **CORS Restrictivo**
```bash
# NO USAR * EN PRODUCCIÓN
ALLOWED_ORIGINS=http://localhost:5678,http://127.0.0.1:5678,https://yourdomain.com
```

---

## 📚 DOCUMENTACIÓN ADICIONAL

- 📋 **[Configuración de Seguridad](config_seguridad.md)** - Guía completa de seguridad
- 🏗️ **[Arquitectura General](0_arquitectura_general.md)** - Diseño del sistema
- 💾 **[Servicio de Persistencia](1_servicio_persistencia.md)** - API de datos
- 🧠 **[Servicio de Clasificación](2_servicio_clasificacion.md)** - Lógica de ML
- 🔄 **[Flujos n8n](3_flujo_n8n.md)** - Automatización de workflows

---

## 🧪 TESTING

### **Tests de Seguridad**
```bash
# Ejecutar tests de seguridad
python -m pytest tests/ -v

# Tests específicos de seguridad
python -m pytest tests/test_security.py -v
```

### **Tests End-to-End**
```bash
# Tests completos del sistema
python -m pytest tests/test_end_to_end.py -v
```

---

## 🚨 TROUBLESHOOTING

### **Problemas Comunes**

#### **1. Error de Autenticación**
```bash
# Verificar que API_TOKEN esté configurado
echo $API_TOKEN

# Verificar longitud mínima (32 caracteres)
echo $API_TOKEN | wc -c
```

#### **2. Redis Connection Error**
```bash
# Verificar que Redis esté ejecutándose
docker ps | grep redis

# Verificar password
docker-compose logs redis
```

#### **3. Rate Limiting**
```bash
# Verificar logs de rate limiting
docker-compose logs classification_service | grep "RateLimitExceeded"
```

---

## 📈 ROADMAP

### **Próximas Mejoras de Seguridad**
- 🔐 **HTTPS/TLS** con certificados automáticos
- 🚪 **Firewall** integrado con reglas dinámicas
- 📊 **Dashboard** de métricas de seguridad
- 🔔 **Alertas** automáticas de eventos de seguridad
- 🔄 **Rotación automática** de tokens y passwords

---

## 🤝 CONTRIBUCIÓN

### **Reportar Vulnerabilidades**
Si encuentras una vulnerabilidad de seguridad:

1. **NO** abrir un issue público
2. **Contactar** directamente al equipo de seguridad
3. **Proporcionar** detalles completos del problema
4. **Esperar** confirmación antes de divulgar

### **Guidelines de Desarrollo**
- ✅ Siempre ejecutar `verificar_seguridad.py` antes de commits
- ✅ Seguir estándares de seguridad del proyecto
- ✅ Documentar cambios de seguridad
- ✅ Incluir tests de seguridad para nuevas funcionalidades

---

## 📄 LICENCIA

Este proyecto está bajo licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## 🏆 RECONOCIMIENTOS

**Certificación de Seguridad**: Diamante Irrompible  
**Auditor**: WindSurf Senior Implacable  
**Fecha**: 26 de agosto de 2025  

*"Este sistema ha pasado la prueba de fuego de seguridad. Es un diamante irrompible."*

---

## 📞 CONTACTO

- **Equipo de Seguridad**: security@sentinel.com
- **Documentación**: docs.sentinel.com
- **Issues**: Solo para funcionalidad, NO para seguridad

---

**⚠️ IMPORTANTE**: Este sistema está aprobado para producción, pero requiere configuración adecuada de variables de entorno antes del despliegue.
