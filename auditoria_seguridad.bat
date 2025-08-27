@echo off
REM 🔐 SCRIPT DE AUDITORÍA DE SEGURIDAD - SISTEMA SENTINEL
REM ⚠️  EJECUTAR REGULARMENTE PARA VERIFICAR SEGURIDAD

echo.
echo ================================================================
echo 🔐 AUDITORÍA DE SEGURIDAD AUTOMATIZADA - SISTEMA SENTINEL
echo ================================================================
echo.

REM Verificar que estemos en el directorio correcto
if not exist "scripts\security_audit.py" (
    echo ❌ ERROR: No se encontró el script de auditoría
    echo    Asegúrate de ejecutar este script desde la raíz del proyecto
    pause
    exit /b 1
)

REM Verificar que Python esté disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está disponible
    echo    Instala Python 3.8+ y agrégalo al PATH
    pause
    exit /b 1
)

REM Verificar que el entorno virtual esté activado
if not defined VIRTUAL_ENV (
    echo ⚠️  ADVERTENCIA: No hay entorno virtual activado
    echo    Se recomienda usar un entorno virtual para la auditoría
    echo.
    set /p continue="¿Continuar sin entorno virtual? (s/N): "
    if /i not "%continue%"=="s" (
        echo ❌ Auditoría cancelada
        pause
        exit /b 1
    )
)

echo ✅ Verificando dependencias...
echo.

REM Instalar dependencias si no están disponibles
python -c "import docker" >nul 2>&1
if errorlevel 1 (
    echo 📦 Instalando dependencia: docker
    pip install docker
)

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo 📦 Instalando dependencia: requests
    pip install requests
)

echo.
echo 🚀 Iniciando auditoría de seguridad...
echo.

REM Ejecutar auditoría
python scripts\security_audit.py

REM Verificar resultado
if errorlevel 1 (
    echo.
    echo 🚨 AUDITORÍA COMPLETADA CON PROBLEMAS CRÍTICOS
    echo    Revisa el reporte y corrige las vulnerabilidades inmediatamente
    echo.
    echo 📋 Próximos pasos:
    echo    1. Revisar el reporte de auditoría generado
    echo    2. Corregir todas las vulnerabilidades críticas
    echo    3. Ejecutar la auditoría nuevamente
    echo    4. NO desplegar en producción hasta que pase la auditoría
) else if errorlevel 2 (
    echo.
    echo ⚠️  AUDITORÍA COMPLETADA CON ADVERTENCIAS
    echo    Se encontraron problemas de seguridad que requieren atención
    echo.
    echo 📋 Próximos pasos:
    echo    1. Revisar el reporte de auditoría generado
    echo    2. Corregir las vulnerabilidades de alta prioridad
    echo    3. Ejecutar la auditoría nuevamente en 24 horas
) else (
    echo.
    echo 🎉 AUDITORÍA COMPLETADA EXITOSAMENTE
    echo    El sistema cumple con los estándares de seguridad básicos
    echo.
    echo 📋 Recomendaciones:
    echo    1. Ejecutar auditoría diariamente en producción
    echo    2. Monitorear logs de seguridad continuamente
    echo    3. Rotar contraseñas cada 90 días
    echo    4. Implementar HTTPS en producción
)

echo.
echo 📁 Reporte guardado en: security_audit_YYYYMMDD_HHMMSS.json
echo.
echo ================================================================
echo 🔐 AUDITORÍA COMPLETADA
echo ================================================================
echo.

pause
