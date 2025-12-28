"""Interfaz interactiva en consola."""  # Explica el modulo

from __future__ import annotations  # Permite tipos adelantados

import os  # Limpia pantalla segun el sistema
import re  # Ayuda a quitar marcas de color
from datetime import date  # Tipo de fecha
from pathlib import Path  # Maneja rutas
from typing import Iterable  # Tipo para listas simples

from .models import ImportantDate, parse_date  # Importa modelo y parser
from .service import DateCounterService  # Importa logica principal
from .storage import JsonStorage  # Importa guardado en disco

DEFAULT_DATA_PATH = Path("data") / "important_dates.json"  # Lugar donde se guardan las fechas


def run() -> None:  # Funcion principal del menu
    """Ejecuta el menu interactivo."""  # Resume la funcion
    service = DateCounterService(JsonStorage(DEFAULT_DATA_PATH))  # Prepara el acceso a datos

    while True:  # Repite hasta salir
        _clear_screen()  # Limpia la consola
        print("")  # Espacio visual
        print("===================================")  # Linea superior
        print("   CONTADOR DE FECHAS IMPORTANTES")  # Titulo
        print("===================================")  # Linea inferior
        print("1) Agregar fecha")  # Opcion 1
        print("2) Ver fechas agregadas")  # Opcion 2
        print("3) Ver proximas")  # Opcion 3
        print("4) Proxima fecha")  # Opcion 4
        print("5) Eliminar fecha")  # Opcion 5
        print("0) Salir")  # Opcion 0
        print("-----------------------------------")  # Separador

        choice = input("Seleccion: ").strip()  # Lee la opcion
        if choice == "0":  # Si quiere salir
            print("Hasta luego.")  # Mensaje de salida
            return  # Termina la funcion
        if choice == "1":  # Si quiere agregar
            _add_date(service)  # Ejecuta la accion
            _pause()  # Pausa para leer
            continue  # Vuelve al menu
        if choice == "2":  # Si quiere ver todas
            _list_dates(service, include_past=True)  # Lista todo
            _pause()  # Pausa para leer
            continue  # Vuelve al menu
        if choice == "3":  # Si quiere ver proximas
            _list_dates(service, include_past=False)  # Lista futuras
            _pause()  # Pausa para leer
            continue  # Vuelve al menu
        if choice == "4":  # Si quiere la proxima
            _show_next(service)  # Muestra la mas cercana
            _pause()  # Pausa para leer
            continue  # Vuelve al menu
        if choice == "5":  # Si quiere eliminar
            _remove_date(service)  # Ejecuta la accion
            _pause()  # Pausa para leer
            continue  # Vuelve al menu

        print("Opcion invalida. Intenta de nuevo.")  # Aviso de error
        _pause()  # Pausa para leer


def _add_date(service: DateCounterService) -> None:  # Agrega una fecha
    """Solicita datos y agrega una nueva fecha."""  # Resume la funcion
    name = input("Nombre: ").strip()  # Lee el nombre
    date_raw = input("Fecha (YYYY-MM-DD): ").strip()  # Lee la fecha
    description = input("Descripcion (opcional): ").strip() or None  # Lee la descripcion

    try:  # Intenta crear la fecha
        item = ImportantDate(name=name, date=parse_date(date_raw), description=description)  # Crea el objeto
        service.add_date(item)  # Guarda el objeto
    except ValueError as exc:  # Si algo falla
        print(f"Error: {exc}")  # Muestra el error
        return  # Sale de la funcion

    print("Fecha agregada.")  # Confirma al usuario


def _list_dates(service: DateCounterService, include_past: bool) -> None:  # Lista fechas
    """Lista fechas y muestra su diferencia con hoy."""  # Resume la funcion
    items = service.list_dates()  # Carga las fechas
    today = date.today()  # Toma el dia actual

    if not include_past:  # Si no quiere ver pasadas
        items = [item for item in items if item.date >= today]  # Filtra futuras

    if not items:  # Si no hay nada
        print("No hay fechas para mostrar.")  # Mensaje simple
        return  # Sale de la funcion

    _print_items(items, today)  # Muestra la tabla


def _show_next(service: DateCounterService) -> None:  # Muestra la mas cercana
    """Muestra la fecha mas cercana."""  # Resume la funcion
    upcoming = service.next_date()  # Busca la mas cercana
    if upcoming is None:  # Si no hay fechas
        print("No hay fechas registradas.")  # Mensaje simple
        return  # Sale de la funcion

    _print_items([upcoming.item], date.today())  # Muestra una sola fecha


def _remove_date(service: DateCounterService) -> None:  # Elimina una fecha
    """Elimina una fecha por nombre."""  # Resume la funcion
    items = service.list_dates()  # Carga las fechas
    if not items:  # Si no hay nada
        print("No hay fechas registradas.")  # Mensaje simple
        return  # Sale de la funcion

    today = date.today()  # Toma el dia actual
    print("Fechas disponibles:")  # Encabezado
    _print_items(items, today)  # Muestra la tabla
    print("")  # Espacio visual
    selection = input("Nombre o N a eliminar: ").strip()  # Pide nombre o numero
    if not selection:  # Si la entrada esta vacia
        print("Nombre invalido.")  # Mensaje de error
        return  # Sale de la funcion

    selected_name = selection  # Usa la entrada como nombre
    if selection.isdigit():  # Si es un numero
        index = int(selection)  # Convierte a entero
        if index < 1 or index > len(items):  # Verifica rango
            print("Numero invalido.")  # Mensaje de error
            return  # Sale de la funcion
        selected_name = items[index - 1].name  # Toma el nombre por indice

    confirm = input(f"Seguro que quieres eliminar '{selected_name}'? (S/N): ").strip()  # Pide confirmacion
    if confirm.lower() != "s":  # Si no confirma
        print("Operacion cancelada.")  # Mensaje de cancelacion
        return  # Sale de la funcion

    removed = service.remove_date(selected_name)  # Intenta eliminar
    if removed:  # Si se elimino
        print(f"Fecha eliminada: {selected_name}")  # Mensaje ok
    else:  # Si no se encontro
        print("No se encontro la fecha.")  # Mensaje de error


def _print_items(items: Iterable[ImportantDate], today: date) -> None:  # Imprime la tabla
    """Imprime fechas con detalle."""  # Resume la funcion
    bar_width = 20  # Ancho de la barra
    rows = []  # Lista de filas
    for index, item in enumerate(items, start=1):  # Recorre las fechas
        days_delta = (item.date - today).days  # Dias que faltan
        total_days = (item.date - item.created_at).days  # Dias totales desde creacion
        if total_days <= 0:  # Evita division por cero
            total_days = 1  # Usa un valor minimo

        elapsed_days = total_days - days_delta  # Dias transcurridos
        progress_percent = (elapsed_days / total_days) * 100  # Porcentaje de avance
        progress_percent = max(min(progress_percent, 100.0), 0.0)  # Limita el rango

        filled_units = round((progress_percent / 100) * bar_width)  # Parte llena
        bar_fill = "#" * filled_units  # Texto de la parte llena
        bar_empty = "-" * (bar_width - filled_units)  # Texto de la parte vacia

        if days_delta < 0:  # Si ya paso
            days_text = f"{abs(days_delta)}d vencido"  # Texto vencido
            bar_text = f"[{bar_fill}{bar_empty}] {progress_percent:5.1f}% {days_text}"  # Barra completa
            bar_text = _red(bar_text)  # Color rojo
        elif days_delta == 0:  # Si es hoy
            bar_text = f"[{bar_fill}{bar_empty}] {progress_percent:5.1f}% HOY"  # Barra hoy
            bar_text = _green(bar_text)  # Color verde
        else:  # Si falta tiempo
            days_text = f"{days_delta}d restantes"  # Texto restante
            bar_text = f"[{bar_fill}{bar_empty}] {progress_percent:5.1f}% {days_text}"  # Barra normal
            if progress_percent >= 66:  # Si esta avanzado
                bar_text = _green(bar_text)  # Verde
            elif progress_percent >= 33:  # Si esta medio
                bar_text = _yellow(bar_text)  # Amarillo
            else:  # Si esta en inicio
                bar_text = _cyan(bar_text)  # Cian

        rows.append(  # Agrega la fila
            (  # Inicia la fila
                str(index),  # Numero de fila
                item.name,  # Nombre de la fecha
                item.date.strftime("%Y-%m-%d"),  # Fecha en texto
                bar_text,  # Barra con porcentaje
            )  # Cierra la fila
        )  # Guarda la fila

    index_width = max(len("N"), max(len(row[0]) for row in rows))  # Ancho de columna N
    name_width = max(len("Nombre"), max(len(row[1]) for row in rows))  # Ancho de nombre
    date_width = len("Fecha")  # Ancho de fecha
    bar_col_width = max(len("Progreso"), max(len(_strip_ansi(row[3])) for row in rows))  # Ancho de barra

    header = (  # Construye el encabezado
        f"{'N'.ljust(index_width)}  "  # Columna N
        f"{'Nombre'.ljust(name_width)}  "  # Columna Nombre
        f"{'Fecha'.ljust(date_width)}  "  # Columna Fecha
        f"{'Progreso'.ljust(bar_col_width)}"  # Columna Progreso
    )  # Termina el encabezado
    print(header)  # Imprime el encabezado
    print("-" * len(header))  # Imprime la linea separadora

    for index, name, date_str, bar_text in rows:  # Recorre filas
        line = (  # Construye la linea
            f"{index.ljust(index_width)}  "  # Numero alineado
            f"{name.ljust(name_width)}  "  # Nombre alineado
            f"{date_str.ljust(date_width)}  "  # Fecha alineada
            f"{_pad_ansi(bar_text, bar_col_width)}"  # Barra alineada
        )  # Termina la linea
        print(line.rstrip())  # Imprime la linea


def _clear_screen() -> None:  # Limpia la consola
    """Limpia la pantalla en Windows o Unix."""  # Resume la funcion
    os.system("cls" if os.name == "nt" else "clear")  # Ejecuta el comando correcto


def _pause() -> None:  # Pausa la pantalla
    """Pausa para que el usuario lea la salida."""  # Resume la funcion
    input("\nPresiona Enter para continuar...")  # Espera al usuario


def _red(text: object) -> str:  # Pinta rojo
    """Pinta el texto en rojo."""  # Resume la funcion
    return f"\x1b[31m{text}\x1b[0m"  # Agrega el color


def _green(text: object) -> str:  # Pinta verde
    """Pinta el texto en verde."""  # Resume la funcion
    return f"\x1b[32m{text}\x1b[0m"  # Agrega el color


def _yellow(text: object) -> str:  # Pinta amarillo
    """Pinta el texto en amarillo."""  # Resume la funcion
    return f"\x1b[33m{text}\x1b[0m"  # Agrega el color


def _cyan(text: object) -> str:  # Pinta cian
    """Pinta el texto en cian."""  # Resume la funcion
    return f"\x1b[36m{text}\x1b[0m"  # Agrega el color


def _strip_ansi(text: str) -> str:  # Quita marcas de color
    """Quita marcas de color para medir el ancho real."""  # Resume la funcion
    return re.sub(r"\x1b\[[0-9;]*m", "", text)  # Elimina las marcas


def _pad_ansi(text: str, width: int) -> str:  # Ajusta el ancho
    """Rellena contando solo lo que se ve."""  # Resume la funcion
    visible = len(_strip_ansi(text))  # Cuenta lo visible
    padding = max(width - visible, 0)  # Calcula el relleno
    return f"{text}{' ' * padding}"  # Devuelve con relleno
