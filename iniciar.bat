@echo off
REM Script de inicio rápido para Windows

echo.
echo ====================================================
echo   LABORATORIO IA - SEPARADOR DE PISTAS CON DEMUCS
echo ====================================================
echo.

REM Verificar si Python está disponible
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no está instalado o no está en PATH
    pause
    exit /b 1
)

echo Iniciando aplicación...
echo.

REM Ejecutar la app
python app.py

pause
