"""Punto de entrada para ejecutar el CLI con python -m."""  # Explica el modulo

from __future__ import annotations  # Permite tipos adelantados

from .cli import run  # Importa la funcion principal


def main() -> None:  # Define la entrada principal
    """Ejecuta el CLI y devuelve el codigo de salida.""" 
    raise SystemExit(run())  # Termina el programa con el codigo de salida


if __name__ == "__main__":  # Evita ejecucion al importar
    main()  # Llama a la funcion principal
