# Arquitectura del Sistema de Clasificación Distribuida para Análisis Policial

## Visión General del Sistema

Este sistema automatiza la clasificación de expedientes policiales utilizando una arquitectura distribuida de nodos autorreplicantes. El sistema procesa 30,000 registros existentes más 300 nuevos semanalmente, clasificando delitos mediante IA híbrida (local + APIs gratuitas) y generando mapas de calor geográficos automáticamente.

## Flujo de Datos Real: Expedientes Policiales Argentinos

### Estructura de Datos de Entrada
**Archivo origen**: Google Sheets con formato `[partido] [año] ([número])` 
Ejemplo: `san martin 2028 (255542)`

**Columnas A-Q (datos originales)**:
- A: id_hecho
- B: nro_registro  
- C: ipp
- D: fecha_carga
- E: hora_carga
- F: dependencia
- G: fecha_inicio_hecho
- H: hora_inicio_hecho
- I: partido_hecho
- J: localidad_hecho
- K: latitud
- L: calle
- M: longitud
- N: altura
- O: entre
- P: calificaciones
- Q: **relato** (columna crítica para clasificación)

### Estructura de Datos de Salida
**Columnas R-AB (clasificación violeta)**:
- R: JURISDICCIÓN
- S: CALIFICACIÓN
- T: MODALIDAD (según referencias de clasificación)
- U: VÍCTIMA (Femenino/Masculino/Ambos)
- V: LESIONADA (SÍ/NO)
- W: IMPUTADOS (Femenino/Masculino/Ambos)
- X: MENOR/MAYOR
- Y: ARMAS (De Fuego/Blanca/Impropia)
- Z: LUGAR (Finca/Vía Pública/Comercio/etc)
- AA: TENTATIVA (Sí/No)
- AB: OBSERVACIÓN

## Arquitectura de Nodos Distribuidos

### 1. Nodo Coordinador Maestro (`CoordinadorMaestro`)
**Responsabilidad**: Gestión estratégica y toma de decisiones del sistema completo.

**Funciones principales**:
- Recibe triggers desde Discord/N8N
- Evalúa carga de trabajo y decide recursos necesarios
- Coordina la creación/destrucción de nodos trabajadores
- Mantiene estado global del sistema
- Gestiona recuperación ante fallos catastróficos

**Especificaciones técnicas**:
- **Entrada**: Comandos de Discord, estado de nodos, métricas de rendimiento
- **Salida**: Instrucciones a planificadores, decisiones de escalado
- **Estado**: Registro de todos los nodos activos, cola de tareas pendientes
- **Logging**: `logs/coordinador_YYYYMMDD.log` con todas las decisiones estratégicas

### 2. Nodos Planificadores (`PlanificadorTareas`)
**Responsabilidad**: División inteligente del trabajo y distribución optimizada.

**Funciones principales**:
- Divide 30K registros en chunks de 500-1000 registros
- Analiza complejidad de cada chunk (simple vs complejo)
- Asigna chunks a trabajadores según especialización
- Mantiene cola de prioridades dinámicas
- Rebalancea trabajo entre nodos sobrecargados

**Algoritmo de división**:
```
Por cada batch de datos:
1. Análisis preliminar de complejidad por registro
2. Agrupación por tipo de delito probable
3. Asignación de prioridad (urgente/normal/background)
4. Creación de paquetes optimizados para procesamiento paralelo
```

**Logging detallado**: Cada decisión de división con justificación y métricas de rendimiento estimadas.

### 3. Nodos Supervisores (`SupervisorSalud`)
**Responsabilidad**: Monitoreo continuo y recuperación automática del sistema.

**Funciones principales**:
- Heartbeat monitoring de todos los nodos cada 30 segundos
- Detección de nodos lentos, colgados o con errores
- Recuperación automática de trabajadores fallidos
- Análisis predictivo de necesidades de escalado
- Alertas inteligentes solo para problemas críticos

**Métricas monitoreadas**:
- Tiempo de respuesta por nodo
- Throughput de procesamiento
- Tasa de errores por tipo
- Uso de memoria y CPU
- Disponibilidad de APIs externas

### 4. Nodo Factory (`FactoriaNodos`)
**Responsabilidad**: Autorreplicación inteligente de nodos trabajadores.

**Proceso de clonación**:
```
Cuando supervisor detecta sobrecarga:
1. Acceso a template_trabajador_optimizado.py
2. Inyección de configuración específica (diccionarios, APIs)
3. Asignación de credenciales rotativas
4. Especialización según tipo de trabajo requerido
5. Registro del nuevo nodo en coordinador maestro
6. Activación y verificación de funcionamiento
```

**Templates de especialización**:
- `TrabajadorSimple`: Solo reglas locales, máxima velocidad
- `TrabajadorComplejo`: Acceso a APIs de IA, mayor precisión
- `TrabajadorMixto`: Híbrido con capacidad de escalado dinámico

### 5. Nodos Trabajadores (`TrabajadorClasificacion`)
**Responsabilidad**: Clasificación real de expedientes con máxima eficiencia.

**Algoritmo de clasificación con referencias policiales argentinas**:
```
Para cada registro del relato (columna Q):
1. FASE LOCAL (0 costo):
   - Aplicar diccionario_legal_argentino.json
   - Clasificar según referencias policiales (HOMICIDIO, ROBO, HURTO, etc.)
   - Determinar modalidad específica (escruche, entradera, motochorros, etc.)
   - Extraer datos de víctima, armas, lugar según relato
   - Confianza >= 85% → Clasificación automática

2. FASE IA (costo mínimo):
   - Solo registros con confianza < 85%
   - Context injection con código penal argentino
   - Prompt específico: "Analiza este relato policial argentino y clasifica según las modalidades oficiales"
   - Rotación automática entre APIs gratuitas
   - Retry logic con fallback entre servicios

3. FASE SALIDA:
   - Completar columnas R-AB con colores violeta
   - Generar nueva Google Sheet clasificada
   - Sincronizar con PostgreSQL para mapas de calor
   - Logging detallado de cada decisión
```

## Sistema de Logging y Auditoría

### Estructura de logs
```
/logs/
├── coordinador/
│   ├── decisiones_YYYYMMDD.log      # Decisiones estratégicas
│   └── escalado_YYYYMMDD.log        # Creación/destrucción de nodos
├── planificadores/
│   ├── division_trabajo_YYYYMMDD.log # División de chunks
│   └── asignaciones_YYYYMMDD.log     # Asignación a trabajadores
├── supervisores/
│   ├── salud_nodos_YYYYMMDD.log      # Estado de todos los nodos
│   └── recuperaciones_YYYYMMDD.log   # Acciones de recuperación
├── trabajadores/
│   ├── clasificaciones_YYYYMMDD.log  # Cada decisión de clasificación
│   ├── api_usage_YYYYMMDD.log        # Uso de APIs externas
│   └── errores_YYYYMMDD.log          # Errores y recuperaciones
└── sistema/
    ├── rendimiento_YYYYMMDD.log      # Métricas globales
    └── auditoria_YYYYMMDD.log        # Log consolidado para auditorías
```

### Formato estándar de log
```json
{
  "timestamp": "2024-07-29T14:30:15.123Z",
  "nodo_id": "trabajador_001",
  "nodo_tipo": "TrabajadorClasificacion",
  "accion": "clasificacion_completada",
  "registro_id": "EXP_2024_001234",
  "metodo_usado": "diccionario_local",
  "confianza": 0.92,
  "tiempo_procesamiento": "0.045s",
  "clasificacion": "hurto_simple",
  "detalles": {
    "keywords_detectadas": ["sustracción", "bien mueble"],
    "patron_aplicado": "hurto_tipo_A",
    "revision_requerida": false
  }
}
```

## Configuración y Diccionarios

### Diccionario Legal Argentino (`config/diccionario_legal.json`)
```json
{
  "homicidios": {
    "homicidio_simple": {
      "keywords_obligatorias": ["muerte", "homicidio", "matare", "fallecimiento"],
      "keywords_excluyentes": ["mujer", "femicidio", "riña", "robo"],
      "modalidad": "homicidio_simple",
      "confianza_base": 0.90
    },
    "femicidio": {
      "keywords_obligatorias": ["mujer", "género", "violencia de género"],
      "contexto_requerido": ["muerte", "asesinato"],
      "modalidad": "femicidio",
      "confianza_base": 0.95
    },
    "intrafamiliar": {
      "keywords_obligatorias": ["familia", "familiar", "doméstico", "pareja", "cónyuge"],
      "contexto_requerido": ["muerte", "homicidio"],
      "modalidad": "intrafamiliar",
      "confianza_base": 0.88
    }
  },
  "robos": {
    "escruche": {
      "keywords_obligatorias": ["ingreso", "vivienda", "ausencia", "propietario"],
      "keywords_excluyentes": ["violencia", "confrontar"],
      "modalidad": "escruche",
      "confianza_base": 0.85
    },
    "entradera": {
      "keywords_obligatorias": ["entrada", "domicilio", "sorprender", "moradores"],
      "contexto_requerido": ["violencia", "robo"],
      "modalidad": "entradera",
      "confianza_base": 0.90
    },
    "motochorros": {
      "keywords_obligatorias": ["motociclista", "moto", "motovehículo"],
      "contexto_requerido": ["robo", "sustracción"],
      "modalidad": "motochorros",
      "confianza_base": 0.92
    },
    "arrebatador": {
      "keywords_obligatorias": ["arrebato", "tirón", "inmediato"],
      "keywords_excluyentes": ["arma", "intimidación"],
      "modalidad": "arrebatador",
      "confianza_base": 0.87
    }
  },
  "hurtos": {
    "hurto_simple": {
      "keywords_obligatorias": ["sustracción", "apoderamiento"],
      "keywords_excluyentes": ["violencia", "fuerza", "intimidación"],
      "modalidad": "hurto_simple",
      "confianza_base": 0.85
    }
  },
  "estafas": {
    "estafa_marketplace": {
      "keywords_obligatorias": ["marketplace", "mercado libre", "venta online"],
      "contexto_requerido": ["engaño", "estafa"],
      "modalidad": "estafa_marketplace",
      "confianza_base": 0.88
    },
    "estafa_cuento_tio": {
      "keywords_obligatorias": ["cuento del tío", "engaño", "buena fe"],
      "contexto_requerido": ["dinero", "inversión"],
      "modalidad": "estafa_cuento_tio",
      "confianza_base": 0.90
    }
  }
}
```

### Sistema de Credenciales Rotativas (`config/api_credentials.json`)
```json
{
  "chatgpt_accounts": [
    {"account_id": "free_001", "requests_used": 45, "limit": 100, "reset_date": "2024-07-30"},
    {"account_id": "free_002", "requests_used": 23, "limit": 100, "reset_date": "2024-07-30"}
  ],
  "claude_accounts": [
    {"account_id": "free_001", "requests_used": 67, "limit": 200, "reset_date": "2024-07-30"}
  ],
  "rotation_strategy": "least_used_first"
}
```

## Integración con Sistemas Externos

### Discord → N8N → Sistema
```
Comando Discord: "!clasificar_expedientes urgente zona_norte"
↓
N8N Webhook recibe comando
↓
N8N activa CoordinadorMaestro con parámetros:
- prioridad: "urgente"
- filtro_geografico: "zona_norte"
- modo: "clasificacion_completa"
```

### Google Sheets → PostgreSQL
```
Sincronización bidireccional:
1. Lectura inicial de 30K registros desde Sheets
2. Clasificación en sistema distribuido
3. Escritura de resultados en nueva sheet con colores violeta
4. Sincronización completa con PostgreSQL
5. Respaldo automático en Google Drive
```

### Generación de Mapas de Calor
```
Proceso automatizado post-clasificación:
1. Agregación de datos por coordenadas geográficas
2. Agrupación por tipo de delito clasificado
3. Cálculo de densidad por zona/partido
4. Generación de mapa interactivo
5. Exportación a múltiples formatos (PNG, HTML, PDF)
```

## Estrategias de Escalabilidad y Recuperación

### Escalado Automático
- **Escalado hacia arriba**: Detección de cola > 1000 tareas → Crear nodos adicionales
- **Escalado hacia abajo**: Cola < 100 tareas por 10 minutos → Reducir nodos
- **Especialización dinámica**: Análisis de tipos de delitos frecuentes → Crear nodos especializados

### Recuperación ante Fallos
- **Fallo de trabajador**: Reasignación automática de tareas en 30 segundos
- **Fallo de planificador**: Coordinador maestro asume funciones temporalmente
- **Fallo de coordinador**: Sistema de elección automática entre supervisores

### Persistencia de Estado
- Checkpoint cada 100 registros procesados
- Estado completo del sistema respaldado cada 15 minutos
- Logs rotados diariamente con compresión automática

## Métricas de Éxito y KPIs

### Rendimiento
- **Throughput objetivo**: 1000 registros clasificados por minuto
- **Precisión objetivo**: >95% en clasificaciones automáticas
- **Disponibilidad**: 99.5% uptime del sistema completo

### Costos
- **API costs**: <$10 USD por mes con cuentas gratuitas rotativas
- **Infraestructura**: Costo cero (ejecución local + servicios gratuitos)
- **Mantenimiento**: <2 horas por mes de intervención manual

### Calidad
- **Trazabilidad**: 100% de decisiones loggeadas y auditables
- **Recuperabilidad**: <5 minutos para recuperación completa ante fallos
- **Escalabilidad**: Manejo automático de 10x incremento en volumen de datos

---

**Nota para Cursor**: Este documento describe un sistema de producción real, no un demo. Cada componente debe implementarse con manejo robusto de errores, logging completo, y capacidades de recuperación automática. El código debe ser mantenible, documentado, y preparado para escalado real con datos de producción.