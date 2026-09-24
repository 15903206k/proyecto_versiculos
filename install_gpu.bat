@echo off
REM Script para instalar CUDA y PyTorch con soporte GPU en Windows
REM Ejecutar desde PowerShell o cmd en la carpeta del proyecto

echo.
echo ====================================
echo  INSTALLER: PyTorch + CUDA GPU
echo ====================================
echo.

REM Verificar si Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado. Asegúrate de que Python esté en PATH.
    pause
    exit /b 1
)

echo [*] Verificando GPU disponible...
python -c "import torch; print('[+] GPU disponible:', torch.cuda.is_available()); print('[+] CUDA version:', torch.version.cuda if torch.cuda.is_available() else 'No'); print('[+] GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'No')"

echo.
echo [*] Detectando NVIDIA GPU drivers...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo [!] NVIDIA GPU drivers NO encontrados.
    echo.
    echo OPCIÓN A: Descargar e instalar drivers manualmente
    echo    - Ir a: https://www.nvidia.com/Download/driverDetails.aspx
    echo    - Descargar driver para tu GPU
    echo    - Instalar y reiniciar
    echo.
    echo OPCIÓN B: Usar GeForce Experience (si tienes NVIDIA GeForce)
    echo    - Descargar: https://www.nvidia.com/en-us/geforce/geforce-experience/
    echo    - Actualizar drivers automáticamente
    echo.
    echo Después de instalar drivers, vuelve a ejecutar este script.
    pause
    exit /b 1
) else (
    echo [+] Drivers NVIDIA encontrados:
    nvidia-smi --query-gpu=name --format=csv,noheader
)

echo.
echo [*] Instalando PyTorch con soporte CUDA 12.1...
python -m pip install --upgrade pip
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

echo.
echo [*] Verificando instalación...
python -c "import torch; print('[+] PyTorch version:', torch.__version__); print('[+] CUDA available:', torch.cuda.is_available()); print('[+] Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"

echo.
echo [*] Reinstalando Demucs con soporte GPU...
python -m pip install --upgrade demucs

echo.
echo ====================================
echo  INSTALACIÓN COMPLETADA!
echo ====================================
echo.
echo Próximo paso:
echo   cd c:\Users\Hp\proyecto_versiculos
echo   py app.py
echo.
pause
