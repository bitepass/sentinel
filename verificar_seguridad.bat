@echo off
chcp 65001 >nul
title 🔒 VALIDADOR DE SEGURIDAD - SISTEMA SENTINEL

echo.
echo ================================================================================
echo 🔒 VALIDADOR DE SEGURIDAD - SISTEMA SENTINEL
echo ================================================================================
echo.

echo Verificando entorno Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Instala Python 3.8+ y agrégalo al PATH.
    pause
    exit /b 1
)

echo ✅ Python encontrado
echo.

echo Verificando dependencias...
pip install python-dotenv requests >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Error instalando dependencias. Continuando...
)

echo ✅ Dependencias verificadas
echo.

echo 🔍 Iniciando validación de seguridad...
echo.

python verificar_seguridad.py

echo.
echo ================================================================================
echo 📋 VALIDACIÓN COMPLETADA
echo ================================================================================
echo.
echo Presiona cualquier tecla para salir...
pause >nul
