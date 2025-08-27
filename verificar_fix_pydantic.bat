@echo off
echo ========================================
echo VERIFICACIÓN POST-FIX PYDANTIC v2
echo ========================================

echo.
echo 1. Verificando sintaxis de Python...
python -m py_compile services/classification_service/app/models.py
if %errorlevel% equ 0 (
    echo ✅ Sintaxis de models.py válida
) else (
    echo ❌ Error de sintaxis en models.py
    exit /b 1
)

echo.
echo 2. Verificando imports de Pydantic...
python -c "from pydantic import BaseModel, Field; print('✅ Pydantic importado correctamente')"
if %errorlevel% neq 0 (
    echo ❌ Error importando Pydantic
    exit /b 1
)

echo.
echo 3. Verificando versión de Pydantic...
python -c "import pydantic; print(f'✅ Pydantic versión: {pydantic.__version__}')"
if %errorlevel% neq 0 (
    echo ❌ Error obteniendo versión de Pydantic
    exit /b 1
)

echo.
echo 4. Verificando sintaxis de pattern en lugar de regex...
findstr /n "pattern=" services/classification_service/app/models.py
if %errorlevel% equ 0 (
    echo ✅ Sintaxis 'pattern=' encontrada correctamente
) else (
    echo ❌ No se encontró sintaxis 'pattern='
    exit /b 1
)

echo.
echo 5. Verificando que no hay 'regex=' residual...
findstr /n "regex=" services/classification_service/app/models.py
if %errorlevel% neq 0 (
    echo ✅ No hay sintaxis 'regex=' residual
) else (
    echo ❌ Se encontró sintaxis 'regex=' residual
    exit /b 1
)

echo.
echo ========================================
echo VERIFICACIÓN COMPLETADA EXITOSAMENTE
echo ========================================
echo.
echo El fix de Pydantic v2 se aplicó correctamente.
echo Ahora puedes proceder con:
echo.
echo 1. docker-compose build --no-cache
echo 2. docker-compose up -d
echo 3. Verificar que los servicios inician sin errores
echo.
pause
