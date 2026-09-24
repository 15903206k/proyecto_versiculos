# Instrucciones de Configuración - Laboratorio IA

## ✅ Lo que fue hecho

1. **Corregido `templates/laboratorio.html`**
   - Eliminado carácter erróneo inicial (`p` antes de `<!DOCTYPE>`)
   - Corregida variable `base` en JavaScript para rutas de stems

2. **Mejorado `procesador_audio.py`**
   - Detección de `demucs` (intenta `python -m demucs` como fallback)
   - Mejor manejo de errores

3. **Implementado Sistema de Cola de Tareas**
   - `tasks.py`: Gestor simple de tareas con threading
   - `cleanup_utils.py`: Limpieza automática de stems antiguos
   - `app.py`: Modificado para encolar tareas en lugar de bloquear

4. **UI Mejorada**
   - Barra de progreso en tiempo real
   - Polling AJAX cada 2 segundos
   - Mensaje de estado dinámico

## 🚀 Cómo ejecutar

### Paso 1: Instalar dependencias (si no las tienes)

```powershell
# Asegúrate de tener Python 3.9+
python --version

# Instalar paquetes necesarios
py -m pip install --upgrade pip
py -m pip install Flask pydub demucs diffq

# Instalar ffmpeg (si no lo tienes)
# Opción A: descargarlo manualmente desde https://ffmpeg.org/download.html
# Opción B: winget install --id Gyan.FFmpeg -e
```

### Paso 2: Ejecutar la app

```powershell
cd c:\Users\Hp\proyecto_versiculos
py app.py

# La app estará en http://127.0.0.1:5000
```

### Paso 3: Probar Laboratorio IA

1. Abre: `http://127.0.0.1:5000/laboratorio`
2. Selecciona una canción de la lista
3. Haz clic en **"Separar Pistas"**
4. Verás una barra de progreso en tiempo real
5. Espera 5-15 minutos (dependiendo del archivo)
6. Una vez completada, se recargará la página automáticamente

## 📊 Flujo de Ejecución

```
Usuario hace clic "Separar Pistas"
         ↓
   POST /separar/<archivo>
         ↓
   TaskManager.create_task()
         ↓
   Thread inicia en background
         ↓
   (Mientras procesa)
   Usuario monitorea con polling /tarea/<task_id>
         ↓
   Mostrar barra de progreso
         ↓
   (Finaliza)
   Página se recarga automáticamente
```

## 🔧 Características Principales

### ✅ Evita Timeouts
- Procesa en threads separados (no bloquea la app)
- El usuario puede cerrar la página y volver después
- Tolerancia para procesos que tardan 30+ minutos

### ✅ Limpieza Automática
- Elimina stems no usados en 30+ días
- Borra carpeta temporal `__demucs_tmp__` al iniciar
- Evita llenar el disco

### ✅ Manejo de Errores
- Captura errores de Demucs y muestra mensajes claros
- Si falta `diffq`, sugiere instalar
- Valida archivos antes de procesar

## 📁 Estructura de Archivos

```
proyecto_versiculos/
├── app.py (MODIFICADO - añadidas imports y endpoints)
├── tasks.py (NUEVO - gestor de tareas)
├── cleanup_utils.py (NUEVO - limpieza de stems)
├── procesador_audio.py (MODIFICADO - mejor detección de demucs)
├── templates/
│   └── laboratorio.html (MODIFICADO - UI con progreso)
├── static/
│   ├── music/ (canciones descargadas)
│   └── stems/ (stems generados por Demucs)
└── data/
    └── tasks/ (estado de tareas - se crea automáticamente)
```

## 🐛 Troubleshooting

### "No se puede encontrar el archivo especificado" (WinError 2)
**Causa:** Falta `ffmpeg` o `demucs` en PATH
**Solución:**
```powershell
ffmpeg -version
py -m demucs --help
```
Si no funcionan, instala según "Paso 1".

### "Demucs CLI falló con code=1"
**Causa:** Falta `diffq` (compilar)
**Solución:**
```powershell
py -m pip install diffq
# Si falla, necesitas Microsoft C++ Build Tools:
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

### La barra de progreso no se actualiza
**Causa:** El navegador cachea los requests
**Solución:** Abre DevTools (F12) → Network → desactiva caché
```powershell
# O abre en modo incógnito:
# Ctrl+Shift+N (Edge/Chrome)
```

### Stems están en `static/stems/__demucs_tmp__` en lugar de `static/stems/<canción>`
**Causa:** Demucs guardó en carpeta temporal
**Solución:** Se limpian automáticamente al reiniciar. Si persiste:
```powershell
Remove-Item -Recurse -Force "static\stems\__demucs_tmp__"
```

## 🌐 Despliegue en Producción

### Con Gunicorn (recomendado)

```powershell
py -m pip install gunicorn

# Ejecutar con 4 workers (ajusta según tu servidor)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Con timeout para operaciones largas:
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 600 app:app
```

### Con Nginx (proxy reverso)

```nginx
server {
    listen 80;
    server_name tu_dominio.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
    }
}
```

## 📝 Variables de Entorno (Opcional)

```powershell
# Para no autenticarse en Hugging Face Hub:
$env:HF_TOKEN = "tu_token_aqui"
# (Opcional: acelera descargas de modelos)

# Para evitar symlinks warning en Windows:
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
```

## 🎯 Próximos Pasos Opcionales

1. **Usar Redis + Celery** (si esperas muchos usuarios simultáneos)
   - Reemplaza tasks.py con Celery
   - Permite escalado horizontal

2. **Limpieza más agresiva** (si el disco es limitado)
   - Ajusta `MAX_STEMS_AGE_DAYS` en `cleanup_utils.py` (ej: 7 en lugar de 30)
   - Agrega cuota máxima de espacio

3. **Integración con API externa** (si no quieres compilar Demucs)
   - Usa API de Moises.ai o similar
   - Elimina dependencia de Demucs local

---

**¿Preguntas?** Revisa los logs en la terminal para ver errores en detalle.
