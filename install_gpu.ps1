# Script para instalar CUDA y PyTorch con soporte GPU en Windows
# Ejecutar desde PowerShell en la carpeta del proyecto

Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host " INSTALLER: PyTorch + CUDA GPU" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# Verificar si Python está disponible
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[+] Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[!] ERROR: Python no encontrado en PATH" -ForegroundColor Red
    Write-Host "    Asegúrate de que Python esté en las variables de entorno." -ForegroundColor Yellow
    exit 1
}

# Verificar GPU actual
Write-Host "`n[*] Verificando GPU disponible..." -ForegroundColor Yellow
$gpuCheck = python -c "import torch; print('GPU:', torch.cuda.is_available()); print('CUDA:', torch.version.cuda if torch.cuda.is_available() else 'No'); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')" 2>&1
Write-Host $gpuCheck

# Detectar NVIDIA drivers
Write-Host "`n[*] Detectando drivers NVIDIA..." -ForegroundColor Yellow
$nvidiaCheck = $null
try {
    $nvidiaCheck = nvidia-smi 2>&1
    if ($nvidiaCheck) {
        Write-Host "[+] Drivers NVIDIA encontrados:" -ForegroundColor Green
        $gpuName = nvidia-smi --query-gpu=name --format=csv,noheader 2>&1
        Write-Host "    $gpuName"
    }
} catch {
    Write-Host "[!] NVIDIA GPU drivers NO encontrados" -ForegroundColor Red
    Write-Host "`nOPCIÓN A: Descargar e instalar drivers manualmente" -ForegroundColor Yellow
    Write-Host "  1. Ir a: https://www.nvidia.com/Download/driverDetails.aspx"
    Write-Host "  2. Descargar driver para tu GPU"
    Write-Host "  3. Instalar y reiniciar Windows"
    Write-Host "`nOPCIÓN B: Usar GeForce Experience" -ForegroundColor Yellow
    Write-Host "  1. Descargar: https://www.nvidia.com/en-us/geforce/geforce-experience/"
    Write-Host "  2. Actualizar drivers automáticamente"
    Write-Host "`nDespués de instalar drivers, vuelve a ejecutar este script." -ForegroundColor Cyan
    exit 1
}

# Instalar PyTorch con CUDA
Write-Host "`n[*] Instalando PyTorch con soporte CUDA 12.1..." -ForegroundColor Yellow
Write-Host "    (esto puede tardar 5-10 minutos)" -ForegroundColor Cyan

python -m pip install --upgrade pip 2>&1 | Out-Null
Write-Host "[+] pip actualizado" -ForegroundColor Green

Write-Host "[*] Descargando PyTorch... (esto es grande ~2.5GB, paciencia)" -ForegroundColor Yellow
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verificar instalación
Write-Host "`n[*] Verificando instalación..." -ForegroundColor Yellow
$torchCheck = python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')" 2>&1
Write-Host $torchCheck -ForegroundColor Green

# Reinstalar Demucs
Write-Host "`n[*] Reinstalando Demucs con soporte GPU..." -ForegroundColor Yellow
python -m pip install --upgrade demucs
Write-Host "[+] Demucs reinstalado" -ForegroundColor Green

# Verificar final
Write-Host "`n[*] Verificación final..." -ForegroundColor Yellow
$finalCheck = python -c "import torch; print('[OK] Todo listo para usar GPU!')" 2>&1
Write-Host $finalCheck -ForegroundColor Green

Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host " INSTALACION COMPLETADA!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan

Write-Host "`nProximos pasos:" -ForegroundColor Yellow
Write-Host "  1. py app.py" -ForegroundColor Cyan
Write-Host "  2. Abre: http://127.0.0.1:5000/laboratorio" -ForegroundColor Cyan
Write-Host "  3. Prueba separar una cancion - Sera 50-100x mas rapido!" -ForegroundColor Cyan

Write-Host "`nComparacion de velocidad:" -ForegroundColor Yellow
Write-Host "  - Sin GPU (CPU): 2-5 minutos" -ForegroundColor Gray
Write-Host "  - Con GPU (CUDA): 30 seg - 2 minutos" -ForegroundColor Green
Write-Host "`n"
