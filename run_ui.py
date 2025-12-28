"""Ejecuta la interfaz interactiva sin instalar el paquete."""  # Explica el archivo

from __future__ import annotations  # Permite tipos adelantados

import sys  # Acceso a la ruta de modulos
from pathlib import Path  # Maneja rutas

PROJECT_ROOT = Path(__file__).resolve().parent  # Carpeta del proyecto
SRC_PATH = PROJECT_ROOT / "src"  # Carpeta con el codigo fuente
sys.path.insert(0, str(SRC_PATH))  # Agrega src al camino de importaciones

from fecha_contador.terminal_ui import run  # noqa: E402  # Importa la interfaz


if __name__ == "__main__":  # Evita ejecucion al importar
    run()  # Llama a la funcion principal
