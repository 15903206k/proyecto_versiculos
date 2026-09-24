"""
Sistema simple de cola de tareas para procesar Demucs sin bloquear.
Usa threading y almacenamiento de estado en JSON.
"""

import json
import threading
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

from procesador_audio import separar_pistas

TASKS_DIR = Path(__file__).parent / "data" / "tasks"
TASKS_DIR.mkdir(parents=True, exist_ok=True)

# Lock para acceso seguro al archivo de tareas
TASKS_LOCK = threading.Lock()


class TaskManager:
    """Gestor simple de tareas para procesamiento en segundo plano."""

    @staticmethod
    def create_task(nombre_archivo: str) -> str:
        """Crea una nueva tarea y devuelve su ID."""
        task_id = str(uuid.uuid4())
        task_data = {
            "id": task_id,
            "nombre_archivo": nombre_archivo,
            "status": "pending",
            "progress": 0,
            "message": "Esperando procesamiento...",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "result": None,
        }
        
        task_file = TASKS_DIR / f"{task_id}.json"
        with TASKS_LOCK:
            task_file.write_text(json.dumps(task_data, indent=2), encoding="utf-8")
        
        # Iniciar procesamiento en thread separado
        thread = threading.Thread(
            target=TaskManager._process_task,
            args=(task_id, nombre_archivo),
            daemon=True,
        )
        thread.start()
        
        return task_id

    @staticmethod
    def _process_task(task_id: str, nombre_archivo: str):
        """Procesa una tarea en background."""
        task_file = TASKS_DIR / f"{task_id}.json"
        
        def update_progress(progress: int, message: str):
            """Callback para actualizar progreso desde separar_pistas."""
            if progress >= 0:
                TaskManager._update_task(task_id, {
                    "progress": min(progress, 99),  # Máximo 99% hasta que complete
                    "message": message,
                })
        
        try:
            # Actualizar estado: iniciando
            TaskManager._update_task(task_id, {
                "status": "processing",
                "progress": 5,
                "message": "Validando archivo...",
                "started_at": datetime.now().isoformat(),
            })
            
            # Ejecutar separación con callback de progreso
            ok, msg = separar_pistas(nombre_archivo, progress_callback=update_progress)
            
            if ok:
                TaskManager._update_task(task_id, {
                    "status": "completed",
                    "progress": 100,
                    "message": msg,
                    "result": "success",
                    "completed_at": datetime.now().isoformat(),
                })
            else:
                TaskManager._update_task(task_id, {
                    "status": "failed",
                    "progress": 0,
                    "message": msg,
                    "result": "error",
                    "completed_at": datetime.now().isoformat(),
                })
        except Exception as e:
            TaskManager._update_task(task_id, {
                "status": "failed",
                "progress": 0,
                "message": f"Error: {str(e)}",
                "result": "error",
                "completed_at": datetime.now().isoformat(),
            })

    @staticmethod
    def _update_task(task_id: str, updates: Dict):
        """Actualiza los datos de una tarea."""
        task_file = TASKS_DIR / f"{task_id}.json"
        
        with TASKS_LOCK:
            if task_file.exists():
                data = json.loads(task_file.read_text(encoding="utf-8"))
                data.update(updates)
                task_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @staticmethod
    def get_task(task_id: str) -> Optional[Dict]:
        """Obtiene el estado de una tarea."""
        task_file = TASKS_DIR / f"{task_id}.json"
        
        with TASKS_LOCK:
            if task_file.exists():
                return json.loads(task_file.read_text(encoding="utf-8"))
        return None

    @staticmethod
    def cleanup_old_tasks(days: int = 7):
        """Limpia tareas completadas hace más de X días."""
        cutoff = datetime.now() - timedelta(days=days)
        
        with TASKS_LOCK:
            for task_file in TASKS_DIR.glob("*.json"):
                try:
                    data = json.loads(task_file.read_text(encoding="utf-8"))
                    completed_at = data.get("completed_at")
                    
                    if completed_at:
                        completed = datetime.fromisoformat(completed_at)
                        if completed < cutoff:
                            task_file.unlink()
                except Exception:
                    pass
