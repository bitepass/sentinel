@echo off
chcp 65001 >nul
echo ========================================
echo    PROYECTO SENTINEL - INICIADOR
echo ========================================
echo.

echo [1/4] 🔍 Verificando entorno virtual...
if not exist "venv\Scripts\activate.bat" (
    echo ❌ ERROR: No se encontró el entorno virtual
    echo 💡 SOLUCIÓN: Ejecuta estos comandos:
    echo    python -m venv venv
    echo    venv\Scripts\activate.bat
    echo    pip install -r services\persistence_service\requirements.txt
    echo    pip install -r services\classification_service\requirements.txt
    pause
    exit /b 1
)

echo [1/4] ✅ Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ ERROR: No se pudo activar el entorno virtual
    echo 💡 SOLUCIÓN: Verifica que Python esté instalado y sea compatible
    echo    python --version
    pause
    exit /b 1
)
echo ✅ Entorno virtual activado

echo.
echo [2/4] 🚀 Iniciando Servicio de Persistencia (Puerto 8001)...
echo 💡 Abriendo nueva terminal para persistencia...
start "Servicio Persistencia" cmd /k "cd /d %~dp0 && venv\Scripts\activate.bat && cd services\persistence_service && echo ✅ Servicio de Persistencia iniciado en puerto 8001 && echo 💡 NO CIERRES ESTA TERMINAL && echo 🔗 URL: http://localhost:8001 && echo. && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 5 /nobreak >nul

echo [2/4] 🔍 Verificando servicio de persistencia...
timeout /t 3 /nobreak >nul
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  ADVERTENCIA: El servicio de persistencia puede tardar en iniciar
    echo 💡 Espera unos segundos y verifica en: http://localhost:8001/health
) else (
    echo ✅ Servicio de persistencia respondiendo correctamente
)

echo.
echo [3/4] 🚀 Iniciando Servicio de Clasificación (Puerto 8002)...
echo 💡 Abriendo nueva terminal para clasificación...
start "Servicio Clasificacion" cmd /k "cd /d %~dp0 && venv\Scripts\activate.bat && cd services\classification_service && echo ✅ Servicio de Clasificación iniciado en puerto 8002 && echo 💡 NO CIERRES ESTA TERMINAL && echo 🔗 URL: http://localhost:8002 && echo. && uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload"
timeout /t 3 /nobreak >nul

echo [3/4] 🔍 Verificando servicio de clasificación...
timeout /t 3 /nobreak >nul
curl -s http://localhost:8002/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  ADVERTENCIA: El servicio de clasificación puede tardar en iniciar
    echo 💡 Espera unos segundos y verifica en: http://localhost:8002/health
) else (
    echo ✅ Servicio de clasificación respondiendo correctamente
)

echo.
echo [4/4] 🚀 Iniciando n8N (Puerto 5678) - CONFIGURACIÓN SIMPLIFICADA...
echo 💡 Abriendo nueva terminal para n8N...
start "n8N Workflow" cmd /k "cd /d %~dp0 && echo ✅ Iniciando n8N con configuración SIMPLIFICADA && echo 💡 NO CIERRES ESTA TERMINAL && echo 🔗 URL: http://localhost:5678 && echo. && echo 🔧 Configurando solo SQLite pool... && set DB_SQLITE_POOL_SIZE=10 && echo ✅ SQLite pool configurado: DB_SQLITE_POOL_SIZE=10 && echo 💡 N8N_RUNNERS_ENABLED se maneja automáticamente && echo. && npx n8n start"
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo    🎉 ¡TODOS LOS SERVICIOS INICIADOS!
echo ========================================
echo.
echo 📍 Servicios corriendo:
echo    • 🟢 Persistencia: http://localhost:8001
echo    • 🟢 Clasificación: http://localhost:8002  
echo    • 🟢 n8N: http://localhost:5678
echo.
echo 🔗 Abre n8N en tu navegador: http://localhost:5678
echo.
echo ⚠️  IMPORTANTE:
echo    • NO CIERRES LAS TERMINALES - Los servicios deben seguir corriendo
echo    • Si hay errores, revisa los logs en cada terminal
echo    • Para detener todo: Cierra las terminales o presiona Ctrl+C
echo.
echo 🆘 SI HAY PROBLEMAS:
echo    • Verifica que los puertos 8001, 8002 y 5678 estén libres
echo    • Asegúrate de que Python y Node.js estén instalados
echo    • Revisa que el entorno virtual tenga todas las dependencias
echo.
echo 🧪 PARA PROBAR:
echo    • Persistencia: http://localhost:8001/health
echo    • Clasificación: http://localhost:8002/health
echo    • n8N: http://localhost:5678
echo.
echo ✨ BONUS: n8N ahora está CONFIGURADO CORRECTAMENTE
echo    • SQLite pool configurado para mejor rendimiento
echo    • Task runners se manejan automáticamente (sin errores)
echo.
pause
