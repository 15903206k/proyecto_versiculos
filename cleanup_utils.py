"""
Utilidades para limpieza automática de stems y archivos temporales.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

STEMS_DIR = Path(__file__).parent / "static" / "stems"
MAX_STEMS_AGE_DAYS = 30  # Borrar stems con más de 30 días sin acceso


def cleanup_old_stems(max_age_days: int = MAX_STEMS_AGE_DAYS):
    """Limpia directorios de stems no accedidos en X días."""
    if not STEMS_DIR.exists():
        return 0
    
    cutoff_time = datetime.now() - timedelta(days=max_age_days)
    removed_count = 0
    
    for stem_folder in STEMS_DIR.iterdir():
        # Saltar carpeta temporal de demucs
        if stem_folder.name == "__demucs_tmp__":
            continue
        
        if not stem_folder.is_dir():
            continue
        
        try:
            # Obtener timestamp de última modificación
            mtime = datetime.fromtimestamp(os.path.getmtime(stem_folder))
            
            if mtime < cutoff_time:
                # Eliminar carpeta y su contenido
                import shutil
                shutil.rmtree(stem_folder)
                removed_count += 1
                print(f"[cleanup] Borrado: {stem_folder.name} (última mod: {mtime})", flush=True)
        except Exception as e:
            print(f"[cleanup] Error limpiando {stem_folder.name}: {e}", flush=True)
    
    return removed_count


def cleanup_temp_demucs():
    """Limpia la carpeta temporal de demucs."""
    temp_folder = STEMS_DIR / "__demucs_tmp__"
    if temp_folder.exists():
        try:
            import shutil
            shutil.rmtree(temp_folder)
            print("[cleanup] Borrada carpeta temporal __demucs_tmp__", flush=True)
            return True
        except Exception as e:
            print(f"[cleanup] Error borrando __demucs_tmp__: {e}", flush=True)
    return False


def get_disk_usage_stems() -> float:
    """Devuelve el tamaño total de stems en MB."""
    if not STEMS_DIR.exists():
        return 0.0
    
    total_size = 0
    for root, dirs, files in os.walk(STEMS_DIR):
        for file in files:
            try:
                total_size += os.path.getsize(os.path.join(root, file))
            except Exception:
                pass
    
    return total_size / (1024 * 1024)  # Convertir a MB
