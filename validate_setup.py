"""
Script de validación y configuración automática antes de iniciar la app.
Asegura que todas las dependencias están correctas.
"""

import subprocess
import sys
import shutil
from pathlib import Path

def check_ffmpeg():
    """Verifica que FFmpeg esté disponible en el PATH."""
    print("🔍 Verificando FFmpeg...", end=" ", flush=True)
    if shutil.which("ffmpeg"):
        print("✅ FFmpeg encontrado")
        return True
    else:
        print("❌ FFmpeg NO ENCONTRADO")
        print("\n⚠️  IMPORTANTE: Instala FFmpeg:")
        print("   1. Descarga desde: https://www.gyan.dev/ffmpeg/builds/")
        print("   2. Instala en C:\\ffmpeg")
        print("   3. Añade C:\\ffmpeg\\bin a tu PATH de Windows")
        print("   4. Reinicia PowerShell")
        return False


def check_demucs():
    """Verifica que Demucs esté instalado."""
    print("🔍 Verificando Demucs...", end=" ", flush=True)
    
    # Intentar importar directamente (más confiable)
    try:
        import demucs
        print(f"✅ Demucs instalado (v{demucs.__version__ if hasattr(demucs, '__version__') else '?'})")
        return True
    except ImportError:
        pass
    
    # Si la importación falla, intentar ejecutar por CLI
    try:
        result = subprocess.run(
            ["demucs", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Demucs instalado (CLI disponible)")
            return True
    except:
        pass
    
    # Si todo falla, intentar instalar
    print("❌ Demucs NO ENCONTRADO")
    print("\n⚠️  Instalando Demucs...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "demucs", "--upgrade"],
            check=True,
            timeout=120  # Timeout más largo para descargas
        )
        print("✅ Demucs instalado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error instalando Demucs: {e}")
        return False


def check_pydub():
    """Verifica que Pydub esté instalado."""
    print("🔍 Verificando pydub...", end=" ", flush=True)
    try:
        import pydub
        print("✅ pydub instalado")
        return True
    except ImportError:
        print("❌ pydub NO ENCONTRADO")
        print("⚠️  Instalando pydub...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pydub"],
                check=True,
                timeout=60
            )
            print("✅ pydub instalado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error instalando pydub: {e}")
            return False


def check_flask():
    """Verifica que Flask esté instalado."""
    print("🔍 Verificando Flask...", end=" ", flush=True)
    try:
        import flask
        print("✅ Flask instalado")
        return True
    except ImportError:
        print("❌ Flask NO ENCONTRADO")
        print("⚠️  Instalando Flask...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "flask"],
                check=True,
                timeout=60
            )
            print("✅ Flask instalado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error instalando Flask: {e}")
            return False


def check_directories():
    """Verifica que existan los directorios necesarios."""
    print("🔍 Verificando estructura de directorios...", end=" ", flush=True)
    base = Path(__file__).parent
    
    dirs = [
        base / "static" / "music",
        base / "static" / "stems",
        base / "data" / "tasks",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    print("✅ Directorios listos")
    return True


def main():
    print("\n" + "="*60)
    print("🚀 VALIDACIÓN PRE-INICIO - Laboratorio IA")
    print("="*60 + "\n")
    
    checks = [
        ("FFmpeg", check_ffmpeg),
        ("Demucs", check_demucs),
        ("pydub", check_pydub),
        ("Flask", check_flask),
        ("Directorios", check_directories),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error en {name}: {e}")
            results.append((name, False))
    
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60)
    
    all_ok = True
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
        if not result:
            all_ok = False
    
    print("="*60 + "\n")
    
    if all_ok:
        print("✅ ¡TODO LISTO! La app puede iniciarse correctamente.")
        print("\n💡 Tip: Primera ejecución descargará modelos (~140MB)")
        print("   Próximas ejecuciones serán 1-2 minutos por canción.\n")
        return 0
    else:
        print("❌ Por favor, instala las dependencias faltantes y reinicia.")
        print("   Mira los mensajes de error arriba ↑\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
