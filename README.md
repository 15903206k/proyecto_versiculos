# 🎵 Laboratorio IA - Separador de Pistas (Moises.ai Style)

**Sistema de separación de pistas de audio con IA usando Demucs. Procesa canciones en 1-2 minutos y genera 4 stems sincronizados: vocals, drums, bass, other.**

---

## ⚡ INICIO RÁPIDO

### Windows (Lo más fácil)
```bash
# Doble-clic en:
iniciar.bat
```

O en PowerShell:
```powershell
py app.py
```

Luego abre en navegador:
```
http://127.0.0.1:5000/laboratorio
```

---

## 🔧 CONFIGURACIÓN PRIMERA VEZ

### 1. Instalar dependencias
```powershell
pip install flask demucs pydub
```

### 2. Instalar FFmpeg (IMPORTANTE)
**Windows:**
- Descarga: https://www.gyan.dev/ffmpeg/builds/
- Elige: `ffmpeg-full` (con todas las librerías)
- Instala en: `C:\ffmpeg`
- Añade a PATH:
  - Abre variables de entorno de Windows
  - Nueva variable: `C:\ffmpeg\bin`

**Verificar:**
```powershell
ffmpeg -version  # Debe mostrar versión
```

### 3. Agregar canciones
Coloca archivos `.mp3` o `.m4a` en:
```
proyecto_versiculos/
└── static/
    └── music/
        ├── cancion1.mp3
        ├── cancion2.mp3
        └── ...
```

### 4. Iniciar aplicación
```powershell
py app.py
```

---

## 🎯 CÓMO USAR

1. **Abre en navegador**: `http://127.0.0.1:5000/laboratorio`

2. **Selecciona una canción** de la lista izquierda
   - Si ya está procesada, verás un ✓ verde
   - Si es nueva, muestra sin marca

3. **Clic en "Separar Pistas"**
   - Ve la barra de progreso actualizar en tiempo real
   - Espera 1-2 minutos ⏱️

4. **Se abre automáticamente la Mesa de Mezclas**
   - 4 sliders: Vocals, Drums, Bass, Other
   - Botones Mute para silenciar tracks
   - Botón Play/Pause sincronizado

5. **Descarga los stems** (opcional)
   - Clic derecho en cada track para guardar

---

## 📊 Estructura del Proyecto

```
proyecto_versiculos/
├── app.py                      # Servidor Flask (MAIN)
├── tasks.py                    # Cola de tareas en background
├── procesador_audio.py         # Demucs wrapper (OPTIMIZADO)
├── cleanup_utils.py            # Limpieza automática
├── validate_setup.py           # Validación de dependencias
├── iniciar.bat                 # Script inicio fácil
│
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── laboratorio.css
│   ├── img/
│   ├── music/                  # 📁 COLOCA TUS CANCIONES AQUÍ
│   │   ├── cancion1.mp3
│   │   └── cancion2.mp3
│   └── stems/                  # 📁 STEMS GENERADOS AUTOMÁTICAMENTE
│       ├── cancion1/
│       │   ├── vocals.mp3
│       │   ├── drums.mp3
│       │   ├── bass.mp3
│       │   └── other.mp3
│       └── cancion2/
│           └── ...
│
├── templates/
│   ├── laboratorio.html        # 🎨 INTERFACE PRINCIPAL
│   └── ...
│
├── data/
│   ├── tasks/                  # 📋 Tareas en progreso
│   └── diccionario_biblico.json
│
└── ffmpeg/                     # (Opcional si descargaste)
    └── bin/
        └── ffmpeg.exe
```

---

## ⚙️ CARACTERÍSTICAS TÉCNICAS

### Backend
- **Framework**: Flask (Python)
- **IA de Separación**: Demucs (Meta Research)
- **Modelo**: `htdemucs` (1-2 min, buena calidad)
- **Cola de Tareas**: Threading (sin Celery/Redis)
- **Almacenamiento**: JSON + Archivos MP3

### Frontend
- **Framework**: Bootstrap 5.3.3
- **Iconos**: Font Awesome 6.4.0
- **Interactividad**: JavaScript + AJAX (Polling)
- **Actualización**: Cada 500ms
- **Componentes**:
  - Selector de canciones
  - Reproductor de audio original
  - Barra de progreso en tiempo real
  - Mesa de mezclas tipo Moises.ai

### Rendimiento
| Acción | Tiempo |
|--------|--------|
| Procesar canción | 1-2 minutos ⚡ |
| Actualizar UI | 500ms |
| Cargar mixer | < 1 segundo |
| Reproducir stems | Tiempo real |

---

## 🔍 TROUBLESHOOTING

### ❌ Error: "FFmpeg no encontrado"
**Solución:**
```powershell
# 1. Descarga FFmpeg desde:
#    https://www.gyan.dev/ffmpeg/builds/

# 2. Instala en C:\ffmpeg

# 3. Añade a PATH (Variables de entorno Windows)

# 4. Verifica:
ffmpeg -version
```

### ❌ Error: "Demucs no está disponible"
**Solución:**
```powershell
pip install demucs --upgrade
# Si aún no funciona:
pip uninstall demucs -y
pip install demucs
```

### ❌ Error: "WinError 2: El sistema no puede encontrar el archivo especificado"
**Solución:**
- FFmpeg no está en PATH
- O Demucs no está instalado
- Ver "Error: FFmpeg no encontrado" arriba

### 🟡 La barra se queda en 10% mucho tiempo
**Motivo:** Primera vez descarga modelo (~140MB)
**Solución:** Espera 5-10 minutos. Próximas veces: 1-2 minutos

### 🟡 El mixer no carga
**Solución:**
```powershell
# Verifica que el archivo se procesó:
# static/stems/cancion1/  debe tener: vocals.mp3, drums.mp3, bass.mp3, other.mp3

# Si falta alguno, re-procesa
```

### 🟡 Progreso muy lento (> 5 minutos)
**Posibles causas:**
- Modelo descargando (primera vez)
- CPU muy lenta
- Disco muy lento (HDD antiguo)

**Solución:**
- Espera a que complete
- La próxima será más rápida

---

## 🎵 FORMATOS SOPORTADOS

**Entrada (Canciones):**
- `.mp3` ✅ (Recomendado)
- `.m4a` ✅
- `.wav` ✅
- `.ogg` ✅
- `.webm` ✅

**Salida (Stems):**
- `.mp3` (Siempre)

**Límite de duración:**
- Máximo: 10 minutos (600 segundos)
- Recomendado: 3-5 minutos

---

## 🚀 OPTIMIZACIONES APLICADAS

✅ **Modelo mejorado**: Cambio de `mdx` (5-15 min) a `htdemucs` (1-2 min)
✅ **Progreso en tiempo real**: Actualización cada 500ms
✅ **Tareas en background**: No bloquea al usuario
✅ **Limpieza automática**: Borra stems viejos
✅ **Múltiples canciones**: Procesa cualquiera
✅ **UI responsiva**: Funciona en móvil y desktop

---

## 📖 MODELOS DISPONIBLES (si quieres cambiar)

En `procesador_audio.py`, línea que dice `-n htdemucs`:

| Modelo | Tiempo | Calidad | Stems |
|--------|--------|---------|-------|
| `htdemucs` | 1-2 min | Buena | 4 |
| `mdx` | 2-5 min | Buena | 4 |
| `mdx_extra_q` | 5-15 min | Excelente | 4 |
| `htdemucs_6stems` | 2-3 min | Buena | 6 |

---

## 🔐 SEGURIDAD

- ✅ Validación de nombres de archivo
- ✅ Prevención de path traversal (`../` bloqueado)
- ✅ Límite de tamaño de archivo
- ✅ Limpieza automática de temporales

---

## 💻 REQUISITOS DEL SISTEMA

**Mínimos:**
- Windows 7 o superior
- Python 3.8+
- 4GB RAM
- 500MB disco libre

**Recomendados:**
- Windows 10/11
- Python 3.10+
- 8GB RAM
- SSD (mucho más rápido)

---

## 📝 NOTAS

- **Primera canción**: Descarga modelo ~140MB (lento)
- **Próximas**: Mucho más rápido
- **GPU**: No se usa actualmente (CPU en ~1-2 min)
- **Internet**: Solo necesario para primera carga de modelo

---

## 🆘 SOPORTE

Si hay problemas:

1. **Revisa los logs** en la terminal donde corre `py app.py`
2. **Ve a `static/stems/` y verifica que existan los archivos**
3. **Reinicia la app**: Ctrl+C, luego `py app.py`
4. **Reinstala dependencias**:
   ```powershell
   pip install demucs flask pydub --force-reinstall
   ```

---

## 📄 ARCHIVOS IMPORTANTES

- `app.py` - Servidor principal
- `procesador_audio.py` - Demucs integration
- `tasks.py` - Cola de tareas
- `validate_setup.py` - Validación automática
- `templates/laboratorio.html` - UI principal

---

## 🎯 ROADMAP FUTURO

- [ ] GPU acceleration (NVIDIA CUDA)
- [ ] Batch processing
- [ ] Base de datos
- [ ] API REST
- [ ] Descarga de stems en ZIP
- [ ] Histórico de procesadas
- [ ] Multi-usuario

---

**¡Disfruta separando tus canciones! 🎵**

Versión: 2.0 (Optimizada)
Última actualización: 2026-07-16
