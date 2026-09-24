"""Descargador de Alabanzas (yt-dlp)

Descarga audio desde una URL usando yt-dlp, con un límite estricto de 50 canciones
en static/music/.

Notas:
- Se intenta descargar en formato nativo reproducible (m4a/mp3) sin forzar conversión.
- Se sanitiza el nombre final para evitar problemas con el reproductor HTML.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Tuple

import yt_dlp


# Ruta del directorio de música (robusta en Windows)
# Nota: usamos Path y rutas relativas al proyecto para evitar issues de directorio actual.
MUSIC_DIR = Path(__file__).resolve().parent / "static" / "music"
LIMIT = 50

# Formatos preferidos (nativos) sin forzar conversión
# yt-dlp intenta elegir un formato con estos contenedores/extensiones.
PREFERRED_AUDIO_EXTS = ("m4a", "mp3")


class LimiteAlcanzadoError(RuntimeError):
    pass


class DescargaError(RuntimeError):
    pass


def _contar_archivos_audio() -> int:
    if not MUSIC_DIR.exists():
        return 0

    # Contamos extensiones de audio razonables en la carpeta.
    exts = {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".webm"}
    return sum(1 for p in MUSIC_DIR.iterdir() if p.is_file() and p.suffix.lower() in exts)


def _sanitizar_nombre(nombre: str) -> str:
    """Sanitiza el nombre del archivo.

    Reglas pedidas:
    - eliminar espacios, tildes, comillas y caracteres raros
    - mantener un conjunto seguro de caracteres para el HTML.
    """
    if not nombre:
        nombre = "alabanza"

    # Normaliza y elimina diacríticos (tildes)
    nombre = unicodedata.normalize("NFKD", nombre)
    nombre = "".join(ch for ch in nombre if not unicodedata.combining(ch))

    # Quita comillas y caracteres problemáticos
    nombre = nombre.replace('"', "").replace("'", "")

    # Elimina espacios
    nombre = nombre.replace(" ", "")

    # Permite solo a-zA-Z0-9-_ .
    # (dejamos punto por la extensión)
    nombre = re.sub(r"[^A-Za-z0-9._-]+", "", nombre)

    # Evita nombres vacíos
    return nombre or "alabanza"


def _elegir_salida_final(salida_path: Path, url: str) -> Path:
    """Renombra el archivo descargado sanitizando el nombre."""
    ext = salida_path.suffix.lower()
    stem = salida_path.stem

    safe_stem = _sanitizar_nombre(stem)

    final_path = salida_path.with_name(f"{safe_stem}{ext}")

    # Evitar colisiones: si existe, agregamos sufijo incremental
    if final_path.exists():
        for i in range(1, 10_000):
            candidate = salida_path.with_name(f"{safe_stem}_{i}{ext}")
            if not candidate.exists():
                final_path = candidate
                break

    if final_path != salida_path:
        salida_path.rename(final_path)

    return final_path


def descargar_audio(url: str) -> Tuple[str, str]:
    """Descarga audio desde una URL.

    Args:
        url: enlace de internet (YouTube, etc.).

    Returns:
        (ruta_relativa, nombre_archivo)

    Raises:
        LimiteAlcanzadoError: si ya hay LIMIT o más canciones.
        DescargaError: si falla la descarga.
    """
    url = (url or "").strip()
    if not url:
        raise DescargaError("URL vacía")

    actual = _contar_archivos_audio()
    if actual >= LIMIT:
        raise LimiteAlcanzadoError("Límite de 50 canciones alcanzado")

    try:
        MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise DescargaError(f"No se pudo crear la carpeta de música: {MUSIC_DIR}. Detalle: {e}")

    if not MUSIC_DIR.exists():
        raise DescargaError(f"No existe la carpeta de música: {MUSIC_DIR}")

    # Template de salida controlado; yt-dlp hará el nombre base.
    # Luego sanitizamos el stem y renombramos.
    outtmpl = str(MUSIC_DIR / "%(title).200B.%(ext)s")

    # Windows: ultra-simple. Pedimos audio nativo (m4a/mp3) y NO conversiones/mezclas.
    # Si el formato nativo no está disponible, yt-dlp fallará y mostrará el error exacto.
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [],
        "ignoreerrors": False,
    }

    try:
        print("yt-dlp comenzando...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        print("yt-dlp terminó extract_info(download=True)")



        # Identificamos el archivo descargado (último en carpeta para ese título/ext)
        title = info.get("title") or "alabanza"

        # ext inferible desde info
        ext = None
        # Preferimos info['ext'] si existe, sino saltamos a buscar.
        if isinstance(info.get("ext"), str):
            ext = info.get("ext")

        downloaded_path = None
        if ext:
            # outtmpl termina en "<title>.ext"
            pattern = f"*{ext}"
            candidates = sorted(MUSIC_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                downloaded_path = candidates[0]

        if not downloaded_path:
            # Fallback: más reciente con audio extension
            exts = {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".webm"}
            candidates = sorted(
                (p for p in MUSIC_DIR.iterdir() if p.is_file() and p.suffix.lower() in exts),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if candidates:
                downloaded_path = candidates[0]

        if not downloaded_path:
            raise DescargaError("No se pudo localizar el archivo descargado")

        final_path = _elegir_salida_final(downloaded_path, url=url)

        # Ruta relativa para construir el front.
        relative = str(final_path.relative_to(Path(__file__).resolve().parent)).replace("\\", "/")
        return relative, final_path.name


    except LimiteAlcanzadoError:
        raise
    except Exception as e:
        print("Error detectado en descargador.py:", str(e), flush=True)
        # Importante: propagamos el error exacto (str(e)) para mostrarlo vía flash en la web.
        raise DescargaError(str(e))



