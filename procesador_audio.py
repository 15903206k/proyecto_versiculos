import traceback
from pathlib import Path
from typing import Optional, Tuple

from pydub import AudioSegment

import subprocess
import shutil
import sys

BASE_DIR = Path(__file__).parent
MUSIC_DIR = BASE_DIR / "static" / "music"
STEMS_DIR = BASE_DIR / "static" / "stems"

ALLOWED_INPUT_EXTS = {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".webm"}
MAX_SECONDS = 600  # límite original


def _safe_filename(nombre_archivo: str) -> Optional[str]:
    nombre_archivo = (nombre_archivo or "").strip()
    if not nombre_archivo:
        return None
    if "/" in nombre_archivo or "\\" in nombre_archivo:
        return None
    return nombre_archivo


def _get_duration_seconds(ruta_archivo: Path) -> float:
    audio = AudioSegment.from_file(str(ruta_archivo))
    return float(len(audio)) / 1000.0


def _expected_outputs(nombre_base: str):
    """Stems esperados por el frontend (4 pistas, mp3)."""
    folder = STEMS_DIR / nombre_base
    vocals = folder / "vocals.mp3"
    drums = folder / "drums.mp3"
    bass = folder / "bass.mp3"
    other = folder / "other.mp3"
    return vocals, drums, bass, other


def _run_demucs_cli(input_path: Path, out_root: Path, progress_callback=None) -> Path:
    """Ejecuta demucs htdemucs (4 stems, rápido: 1-2 min) vía CLI y devuelve folder donde están los stems.

    Comando exacto:
    ['demucs', '-n', 'htdemucs', '--mp3', ruta_archivo, '-o', ruta_salida]
    
    Modelos disponibles:
    - htdemucs: 1-2 minutos (RECOMENDADO - rápido y buena calidad)
    - mdx: 2-5 minutos (equilibrado)
    - mdx_extra_q: 5-15 minutos (muy lento, excelente calidad)
    
    Args:
        progress_callback: función(progress_int, message_str) para reportar progreso en tiempo real
    """
    out_root.mkdir(parents=True, exist_ok=True)

    # Prefer direct 'demucs' executable if available, otherwise try running as a module
    base_cmd = ["-n", "htdemucs", "--mp3", str(input_path), "-o", str(out_root)]

    if shutil.which("demucs"):
        cmd = ["demucs"] + base_cmd
    else:
        # Fallback: try running via the current Python interpreter: `python -m demucs ...`
        cmd = [sys.executable, "-m", "demucs"] + base_cmd

    print(f"[demucs-cli] Running: {' '.join(cmd)}", flush=True)
    
    # Usar Popen para leer output en tiempo real
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Combinar stderr con stdout
        text=True,
        bufsize=1  # Line buffered
    )
    
    try:
        line_count = 0
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            line = line.strip()
            if line:
                print(f"[demucs] {line}", flush=True)
                line_count += 1
                
                # Reportar progreso cada cierta cantidad de líneas
                # Demucs suele imprimir ~40-100 líneas durante procesamiento
                if progress_callback and line_count % 10 == 0:
                    # Calcular progreso: 30-65% es rango de Demucs
                    progress = min(30 + (line_count * 2), 65)
                    progress_callback(progress, f"Procesando con Demucs... ({line_count} etapas)")
        
        # Esperar a que el proceso termine
        returncode = process.wait()
        
        if returncode != 0:
            tail = "Demucs completó pero reportó error"
            raise RuntimeError(f"Demucs CLI falló con code={returncode}. stderr tail: {tail}")
        
        if progress_callback:
            progress_callback(65, "Demucs completado. Buscando stems...")

    except Exception as e:
        if process.poll() is None:
            process.kill()
        raise e

    # Buscar directorio que contiene los 4 stems
    for sub in out_root.rglob("vocals.mp3"):
        base = sub.parent
        if (
            (base / "vocals.mp3").exists()
            and (base / "drums.mp3").exists()
            and (base / "bass.mp3").exists()
            and (base / "other.mp3").exists()
        ):
            return base

    raise FileNotFoundError(
        "No se encontraron vocals.mp3/drums.mp3/bass.mp3/other.mp3 en la salida demucs."
    )


def separar_pistas(nombre_archivo: str, progress_callback=None) -> Tuple[bool, str]:
    """Separa 4 stems (vocals/drums/bass/other) con Demucs vía CLI.
    
    Args:
        nombre_archivo: nombre del archivo a procesar
        progress_callback: función opcional para reportar progreso: callback(progress_percent, message)
    """
    try:
        nombre_archivo = _safe_filename(nombre_archivo)
        if not nombre_archivo:
            return False, "Error: nombre de archivo inválido."

        input_path = MUSIC_DIR / nombre_archivo
        if not input_path.exists() or not input_path.is_file():
            return False, f"Error: no existe {input_path}"

        if input_path.suffix.lower() not in ALLOWED_INPUT_EXTS:
            return False, "Error: formato de audio no soportado."

        try:
            dur = _get_duration_seconds(input_path)
            if dur > MAX_SECONDS:
                return False, (
                    f"Error: la alabanza excede el máximo permitido (MAX_SECONDS={MAX_SECONDS}s). "
                    f"Duración actual: {dur:.1f}s"
                )
        except Exception:
            pass

        nombre_base = input_path.stem
        out_folder = STEMS_DIR / nombre_base
        vocals, drums, bass, other = _expected_outputs(nombre_base)

        # limpiar
        for p in [vocals, drums, bass, other]:
            out_folder.mkdir(parents=True, exist_ok=True)
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

        if progress_callback:
            progress_callback(20, "Limpieza completada. Iniciando Demucs...")

        # Ejecutar Demucs: -o se usa como raíz donde demucs crea carpeta(s)
        out_root = out_folder.parent / "__demucs_tmp__"
        stems_dir = _run_demucs_cli(input_path=input_path, out_root=out_root, progress_callback=progress_callback)

        if progress_callback:
            progress_callback(70, "Demucs completado. Copiando stems...")

        # copiar stems finales al folder correcto
        for idx, name in enumerate(["vocals", "drums", "bass", "other"]):
            src = stems_dir / f"{name}.mp3"
            dst = out_folder / f"{name}.mp3"
            if not src.exists():
                raise FileNotFoundError(f"Missing stem {src}")
            shutil.copy2(src, dst)
            
            # Actualizar progreso mientras copiamos
            if progress_callback:
                pct = 70 + (idx + 1) * 7  # 77, 84, 91, 98
                progress_callback(pct, f"Copiando {name}.mp3...")

        vocals, drums, bass, other = _expected_outputs(nombre_base)
        if not all(p.exists() for p in [vocals, drums, bass, other]):
            return False, (
                "Error: la separación no generó los 4 stems esperados "
                "(vocals/drums/bass/other)."
            )

        if progress_callback:
            progress_callback(100, "✓ Separación completada correctamente")

        return True, "Separación completada correctamente (4 stems)."

    except Exception as e:
        print("Error separar_pistas:", e, flush=True)
        print(traceback.format_exc(), flush=True)
        if progress_callback:
            progress_callback(-1, f"Error: {str(e)}")
        return False, f"Error al separar pistas: {e}"

