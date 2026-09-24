from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, send_from_directory

import os
import json
import shutil
from pathlib import Path


# Validar dependencias antes de hacer nada
print("\n" + "="*60)
print("🔍 VALIDANDO CONFIGURACIÓN...")
print("="*60)

# Importar y ejecutar validación
try:
    from validate_setup import check_ffmpeg, check_demucs, check_pydub, check_directories
    
    checks_ok = all([
        check_ffmpeg(),
        check_demucs(),
        check_pydub(),
        check_directories(),
    ])
    
    if not checks_ok:
        print("\n⚠️  ADVERTENCIA: Algunas dependencias podrían no estar correctas.")
        print("   La app intentará continuar, pero podría haber errores.\n")
except Exception as e:
    print(f"\n⚠️  No se pudo validar: {e}\n")

print("="*60 + "\n")

from procesador_audio import separar_pistas, MUSIC_DIR, STEMS_DIR
from tasks import TaskManager
from cleanup_utils import cleanup_old_stems, cleanup_temp_demucs, get_disk_usage_stems

app = Flask(__name__)

# Limpiar archivos temporales al iniciar
try:
    cleanup_temp_demucs()
    cleanup_old_stems(max_age_days=30)
except Exception as e:
    print(f"[cleanup] Error inicial: {e}", flush=True)


# Diccionario de datos con las categorías y versículos solicitados (para la portada)
VERSICULOS = {
    "Fe": [
        {"texto": "Es, pues, la fe la certeza de lo que se espera, la convicción de lo que no se ve.", "cita": "Hebreos 11:1"},
        {"texto": "Jesús le dijo: Si puedes creer, al que cree todo le es posible.", "cita": "Marcos 9:23"},
    ],
    "Confianza": [
        {"texto": "Jehová es mi luz y mi salvación; ¿de quién temeré?", "cita": "Salmo 27:1"},
        {"texto": "Fíaos de Jehová para siempre, porque en Jehová el Señor está la fortaleza de los siglos.", "cita": "Isaías 26:4"},
    ],
    "Para la Familia": [
        {"texto": "Cree en el Señor Jesucristo, y serás salvo tú y tu casa.", "cita": "Hechos 16:31"},
        {"texto": "Yo y mi casa serviremos a Jehová.", "cita": "Josué 24:15"},
    ],
    "Para los Jóvenes": [
        {"texto": "Ninguno tenga en poco tu juventud, sino sé ejemplo de los creyentes en palabra, conducta, amor, espíritu, fe y pureza.", "cita": "1 Timoteo 4:12"},
        {"texto": "¿Con qué limpiará el joven su camino? Con guardar tu palabra.", "cita": "Salmo 119:9"},
    ],
    "Para los Padres": [
        {"texto": "Instruye al niño en su camino, y aun cuando fuere viejo no se apartará de él.", "cita": "Proverbios 22:6"},
        {"texto": "Y vosotros, padres, no provoquéis a ira a vuestros hijos, sino criadlos en disciplina y amonestación del Señor.", "cita": "Efesios 6:4"},
    ],
    "Alabanzas": [
        {"texto": "Alabadle con salterio y arpa. Alabadle con pandero y danza.", "cita": "Salmo 150:3-4"},
        {"texto": "Cantad a Jehová cántico nuevo; su alabanza sea en la congregación de los santos.", "cita": "Salmo 149:1"},
    ],
}


# ======= CHATBOT CON DICCIONARIO EXTERNO =======
DICC_PATH = Path(__file__).parent / "data" / "diccionario_biblico.json"


def cargar_diccionario():
    try:
        return json.loads(DICC_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def normalizar(texto: str) -> str:
    return (texto or "").lower().strip()


def formatear_versiculos(versiculos):
    lineas = []
    for v in versiculos:
        texto = v.get("texto", "")
        cita = v.get("cita", "")
        lineas.append(f"📖 {texto}\n— {cita}")
    return "\n\n".join(lineas)


DICCIONARIO_BIBLICO = cargar_diccionario()

DEFAULT_RESPUESTA = (
    "Entiendo. Cuéntame qué necesitas hoy sobre la Biblia "
    "(ej: amor, fe, esperanza, paz, perdón, ansiedad, tristeza, familia, jóvenes, oración) "
    "y te respondo con versículos bíblicos. 🙏"
)


@app.route('/')
def home():
    # Portada
    return render_template('index.html', categorias=VERSICULOS)


@app.route('/ninos')
def ninos():
    return render_template('libro.html')


@app.route('/trivia')
def trivia():
    return render_template('trivia.html')


@app.route('/mapa')
def mapa():
    return render_template('mapa.html')


@app.route('/alabanzas')
def alabanzas():
    return render_template('alabanzas.html')


@app.route('/mis_alabanzas')
def mis_alabanzas():
    music_dir = Path(__file__).parent / 'static' / 'music'
    canciones_descargadas = []

    if music_dir.exists():
        # Solo .mp3 y .m4a
        for p in music_dir.iterdir():
            if p.is_file() and p.suffix.lower() in {'.mp3', '.m4a'}:
                canciones_descargadas.append(p.name)

    # Orden estable para una mejor experiencia
    canciones_descargadas.sort(key=lambda x: x.lower())

    return render_template('reproductor_descargas.html', canciones=canciones_descargadas)



@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    mensaje_usuario = normalizar(data.get('mensaje'))

    # Si el diccionario no carga, devolvemos respuesta default
    if not DICCIONARIO_BIBLICO:
        return jsonify({"respuesta": DEFAULT_RESPUESTA})

    mejor_tema = None
    mejor_score = 0

    # Score simple: cada keyword encontrada suma 1
    for tema, info in DICCIONARIO_BIBLICO.items():
        keywords = info.get("keywords", [])
        score = 0
        for kw in keywords:
            kw_n = normalizar(kw)
            if kw_n and kw_n in mensaje_usuario:
                score += 1
        if score > mejor_score:
            mejor_score = score
            mejor_tema = tema

    if not mejor_tema:
        return jsonify({"respuesta": DEFAULT_RESPUESTA})

    versiculos = DICCIONARIO_BIBLICO.get(mejor_tema, {}).get("versiculos", [])
    if not versiculos:
        return jsonify({"respuesta": DEFAULT_RESPUESTA})

    return jsonify({"respuesta": formatear_versiculos(versiculos)})


from descargador import descargar_audio

app.secret_key = 'cambia-esto-por-una-clave-segura'


@app.route('/eliminar_alabanza/<nombre_archivo>', methods=['POST'])
def eliminar_alabanza(nombre_archivo):
    # Solo permitir nombres simples (evita path traversal)
    nombre_archivo = (nombre_archivo or '').strip()
    if not nombre_archivo or '/' in nombre_archivo or '\\' in nombre_archivo:
        flash('Error al eliminar la alabanza (nombre inválido)', 'error')
        return redirect(url_for('mis_alabanzas'))

    music_dir = Path(__file__).parent / 'static' / 'music'
    archivo = music_dir / nombre_archivo

    try:
        if music_dir.exists() and archivo.exists() and archivo.is_file():
            os.remove(archivo)
            flash('Alabanza eliminada correctamente', 'success')
        else:
            flash('No se encontró la alabanza para eliminar', 'error')
    except Exception as e:
        flash(f'Error al eliminar la alabanza: {e}', 'error')

    return redirect(url_for('mis_alabanzas'))


@app.route('/descargar', methods=['GET', 'POST'])
def descargar():
    LIMITE = 50
    MUSIC_DIR = Path(__file__).parent / 'static' / 'music'

    def contar_audio():
        if not MUSIC_DIR.exists():
            return 0
        exts = {'.mp3', '.m4a', '.aac', '.wav', '.ogg', '.webm'}
        return sum(1 for p in MUSIC_DIR.iterdir() if p.is_file() and p.suffix.lower() in exts)

    if request.method == 'GET':
        actual = contar_audio()
        return render_template('vista_descarga.html', actual=actual, limite=LIMITE)

    url = (request.form.get('url') or '').strip()
    if not url:
        flash('Error al descargar', 'error')
        return redirect('/descargar')

    try:
        print("Recibiendo URL:", url, flush=True)
        print("Iniciando descarga (yt-dlp)...", flush=True)
        descargar_audio(url)
        print("Descarga OK. Redirigiendo...", flush=True)
        flash('¡Alabanza descargada con éxito!', 'success')
        return redirect(url_for('mis_alabanzas'))
    except Exception as e:
        # Mensajes requeridos + mostrar error real para diagnosticar.
        detalle = str(e)
        print("Error en /descargar:", detalle, flush=True)
        if 'Límite' in detalle or 'limite' in detalle.lower():
            flash('Límite de 50 canciones alcanzado', 'error')
        else:
            flash(detalle, 'error')
        return redirect('/descargar')





@app.route('/stems_disponibles')
def stems_disponibles():
    """Lista persistente de canciones ya separadas (stems existentes)."""
    stems_base = []
    if STEMS_DIR.exists():
        for folder in STEMS_DIR.iterdir():
            if not folder.is_dir():
                continue
            base = folder.name
            # Consideramos separada si existe other.mp3
            if (folder / 'other.mp3').exists():
                stems_base.append(base)

    stems_base.sort(key=lambda x: x.lower())
    return jsonify({"ok": True, "stems": stems_base})


@app.route('/download_other/<nombre_archivo>')
def download_other(nombre_archivo):
    """Descarga el stem other.mp3 para una canción ya separada."""
    nombre_archivo = (nombre_archivo or '').strip()
    if not nombre_archivo or '/' in nombre_archivo or '\\' in nombre_archivo:
        return jsonify({"ok": False, "error": "Nombre inválido"}), 400

    # nombre_archivo puede llegar como "base" (sin extensión) o como "archivo.m4a".
    # OJO: si el base contiene puntos (ej: PadredeamorPablo.S.2007), Path(...).stem lo truncaría.
    nombre_archivo = (nombre_archivo or '').strip()

    # Intento 1: usar tal cual como base de carpeta
    folder = STEMS_DIR / nombre_archivo

    # Intento 2: fallback usando stem (solo si el intento 1 no existe)
    if not folder.exists():
        candidato_base = Path(nombre_archivo).stem
        folder = STEMS_DIR / candidato_base

    stem_path = folder / 'other.mp3'
    if not stem_path.exists():
        return jsonify({"ok": False, "error": "Stem other no encontrado"}), 404

    return send_from_directory(directory=str(folder), path='other.mp3', as_attachment=True)


@app.route('/laboratorio')
def laboratorio():

    # Lista archivos disponibles en static/music/
    canciones = []
    if MUSIC_DIR.exists():
        for p in MUSIC_DIR.iterdir():
            if p.is_file() and p.suffix.lower() in {'.mp3', '.m4a'}:
                canciones.append(p.name)
    canciones.sort(key=lambda x: x.lower())

# Detecta stems existentes en static/stems/<base>/ (4 pistas mp3)
    stems_exist = {}  # base -> {"vocals": bool, "drums": bool, "bass": bool, "other": bool}
    if STEMS_DIR.exists():
        for folder in STEMS_DIR.iterdir():
            if folder.is_dir():
                base = folder.name
                vocals_ok = (folder / "vocals.mp3").exists()
                drums_ok = (folder / "drums.mp3").exists()
                bass_ok = (folder / "bass.mp3").exists()
                other_ok = (folder / "other.mp3").exists()
                stems_exist[base] = {
                    "vocals": vocals_ok,
                    "drums": drums_ok,
                    "bass": bass_ok,
                    "other": other_ok,
                }


# Si viene base (desde “Usar en mesa”), úsalo tal cual.
    base_arg = (request.args.get('base') or '').strip()

    # nombre_archivo solo se usa para mostrar el audio original y para el input hidden.
    nombre_archivo = (request.args.get('nombre_archivo') or '').strip()
    if not nombre_archivo and canciones:
        nombre_archivo = canciones[0]

    procesado = False
    base = None
    if base_arg:
        base = base_arg
    elif nombre_archivo:
        base = Path(nombre_archivo).stem

    if base:
        procesado = bool(
            stems_exist.get(base, {}).get('vocals')
            and stems_exist.get(base, {}).get('drums')
            and stems_exist.get(base, {}).get('bass')
            and stems_exist.get(base, {}).get('other')
        )



    return render_template(
        "laboratorio.html",
        canciones=canciones,
        stems_exist=stems_exist,
        nombre_archivo=nombre_archivo,
        procesado=procesado,
    )



def _enlistar_separar(nombre_archivo: str):
    """Encola la tarea de separación en lugar de ejecutarla directamente (evita timeout)."""
    nombre_archivo = (nombre_archivo or '').strip()

    # Validar archivo básicamente
    if not nombre_archivo or '/' in nombre_archivo or '\\' in nombre_archivo:
        return jsonify({"ok": False, "error": "Nombre de archivo inválido"}), 400

    music_path = MUSIC_DIR / nombre_archivo
    if not music_path.exists():
        return jsonify({"ok": False, "error": "Archivo de música no encontrado"}), 404

    # Crear tarea en cola
    try:
        task_id = TaskManager.create_task(nombre_archivo)
        return jsonify({
            "ok": True,
            "task_id": task_id,
            "message": f"Separación iniciada. ID: {task_id[:8]}. Esto puede tardar 2-5 minutos."
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/separar', methods=['POST'])
def separar_post():
    data = request.get_json(silent=True) or {}
    nombre_archivo = (data.get('nombre_archivo') or '').strip()
    return _enlistar_separar(nombre_archivo)


@app.route('/separar/<nombre_archivo>', methods=['POST'])
def separar(nombre_archivo):
    return _enlistar_separar(nombre_archivo)



@app.route('/tarea/<task_id>')
def tarea_status(task_id):
    """Endpoint AJAX para obtener el estado de una tarea de separación."""
    # Buscar el archivo de tarea por prefijo
    from pathlib import Path
    tasks_dir = Path(__file__).parent / "data" / "tasks"
    
    if tasks_dir.exists():
        for task_file in tasks_dir.glob(f"{task_id}*.json"):
            task = json.loads(task_file.read_text(encoding="utf-8"))
            return jsonify(task)
    
    # Si no hay archivo, devolver 404
    return jsonify({"error": "Tarea no encontrada"}), 404


@app.route('/eliminar_separada', methods=['POST'])
def eliminar_separada():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"ok": False, "error": "No se recibió JSON válido"}), 400

    data = data or {}
    nombre_cancion = (data.get('nombre_cancion') or '').strip()

    if not nombre_cancion or '/' in nombre_cancion or '\\' in nombre_cancion:
        return jsonify({"ok": False, "error": "Nombre de canción inválido"}), 400

    # Los stems “ya separadas” se listan desde STEMS_DIR (= static/stems/).
    # Por eso el borrado debe apuntar al mismo lugar.
    base_dir = STEMS_DIR / nombre_cancion


    try:
        print(f"[eliminar_separada] recibido nombre_cancion={nombre_cancion}", flush=True)
        print(f"[eliminar_separada] carpeta={base_dir}", flush=True)

        if not base_dir.exists() or not base_dir.is_dir():
            return jsonify({"ok": False, "error": "La alabanza separada no existe"}), 404

        shutil.rmtree(str(base_dir))
        print(f"[eliminar_separada] OK borrado {base_dir}", flush=True)
        return jsonify({"ok": True})
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[eliminar_separada] ERROR: {e}\n{tb}", flush=True)
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/descargar_stem/<tipo>/<nombre_archivo>')
def descargar_stem(tipo, nombre_archivo):
    tipo = (tipo or "").strip().lower()
    nombre_archivo = (nombre_archivo or "").strip()

    # stem base por nombre sin extensión
    base = Path(nombre_archivo).stem

    if tipo == "vocals" or tipo == "voz":
        filename = "vocals.mp3"
    elif tipo == "drums":
        filename = "drums.mp3"
    elif tipo == "bass":
        filename = "bass.mp3"
    elif tipo == "other" or tipo == "instrumental" or tipo == "instrumento" or tipo == "instrumentos":
        filename = "other.mp3"

    else:
        flash("Tipo de stem inválido.", "error")
        return redirect(url_for("laboratorio"))

    folder = STEMS_DIR / base
    if not folder.exists():
        flash("Error: stems no generados para este archivo.", "error")
        return redirect(url_for("laboratorio"))

    stem_path = folder / filename
    if not stem_path.exists():
        flash("Error: stem no encontrado para descargar.", "error")
        return redirect(url_for("laboratorio"))

    return send_from_directory(
        directory=str(folder),
        path=filename,
        as_attachment=True,
    )


if __name__ == '__main__':
    # En producción, usar gunicorn: gunicorn -w 4 -b 0.0.0.0:5000 app:app
    # debug=False evita que se creen múltiples procesos / reinicios automáticos
    app.run(debug=False, threaded=True, port=5000)


