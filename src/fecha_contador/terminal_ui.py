"""Interfaz interactiva en consola."""  # Explica el modulo

from __future__ import annotations  # Permite tipos adelantados

import os  # Limpia pantalla segun el sistema
import re  # Ayuda a quitar marcas de color
from calendar import monthrange  # Dias por mes
from datetime import date, datetime  # Tipos de fecha y hora
from pathlib import Path  # Maneja rutas
from typing import Iterable, Optional  # Tipo para listas simples

import questionary  # Prompts interactivos
from rich.console import Console  # Consola rica
from rich.table import Table  # Tablas ricas
from rich.progress import ProgressBar  # Barras de progreso ricas
from rich.panel import Panel  # Paneles para decoracion
from rich.text import Text  # Texto rico
from rich.align import Align  # Alineacion

from .models import ImportantDate, parse_datetime  # Importa modelo y parser
from .service import DateCounterService  # Importa logica principal
from .storage import JsonStorage  # Importa guardado en disco

DEFAULT_DATA_PATH = Path("data") / "important_dates.json"  # Lugar donde se guardan las fechas
console = Console()  # Instancia global de consola rich


def _coerce_to_date(value: date | datetime) -> date:
    """Normaliza datetime o date a date para comparar por dia."""
    return value.date() if isinstance(value, datetime) else value


def _ask_date_with_lists(today: date) -> Optional[datetime]:
    """Permite seleccionar una fecha guiada por listas."""
    current_year = today.year
    year_choices = [
        questionary.Choice(f"{current_year}", current_year),
        questionary.Choice(f"{current_year + 1}", current_year + 1),
        questionary.Choice(f"{current_year + 2}", current_year + 2),
        questionary.Choice("Otro año...", "custom"),
    ]
    selected_year = questionary.select("Selecciona el año:", choices=year_choices).ask()
    if selected_year is None:
        return None
    if selected_year == "custom":
        custom_year = questionary.text(
            "Escribe el año (YYYY):",
            validate=lambda text: True if re.match(r"^\d{4}$", text) else "Año inválido",
        ).ask()
        if custom_year is None:
            return None
        selected_year = int(custom_year)

    month_names = [
        "01 - Enero", "02 - Febrero", "03 - Marzo", "04 - Abril",
        "05 - Mayo", "06 - Junio", "07 - Julio", "08 - Agosto",
        "09 - Septiembre", "10 - Octubre", "11 - Noviembre", "12 - Diciembre",
    ]
    month_choice = questionary.select("Selecciona el mes:", choices=[
        questionary.Choice(name, index + 1) for index, name in enumerate(month_names)
    ]).ask()
    if month_choice is None:
        return None

    days_in_month = monthrange(int(selected_year), int(month_choice))[1]
    weekday_names = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    day_choices = []
    for day in range(1, days_in_month + 1):
        weekday = weekday_names[datetime(int(selected_year), int(month_choice), day).weekday()]
        day_choices.append(questionary.Choice(f"{day:02d} ({weekday})", day))

    selected_day = questionary.select("Selecciona el día:", choices=day_choices).ask()
    if selected_day is None:
        return None

    add_time = questionary.confirm("¿Quieres agregar hora/minuto?", default=False).ask()
    hour = minute = 0
    if add_time:
        time_raw = questionary.text(
            "Hora (HH:MM):",
            validate=lambda text: True if re.match(r"^\d{2}:\d{2}$", text) else "Usa HH:MM",
        ).ask()
        if time_raw is None:
            return None
        hour, minute = map(int, time_raw.split(":"))

    return datetime(int(selected_year), int(month_choice), int(selected_day), hour, minute)


def run() -> None:  # Funcion principal del menu
    """Ejecuta el menu interactivo."""  # Resume la funcion
    service = DateCounterService(JsonStorage(DEFAULT_DATA_PATH))  # Prepara el acceso a datos

    while True:  # Repite hasta salir
        _clear_screen()  # Limpia la consola
        
        console.print(
            Panel(
                Align.center(
                    "[bold cyan]CONTADOR DE FECHAS IMPORTANTES[/bold cyan]",
                    vertical="middle"
                ),
                subtitle="[italic]Organiza tus momentos especiales[/italic]",
                padding=(1, 2)
            )
        )

        choice = questionary.select(
            "¿Qué deseas hacer?",
            choices=[
                questionary.Choice("1) Agregar fecha", "1"),
                questionary.Choice("2) Ver fechas agregadas", "2"),
                questionary.Choice("3) Ver próximas", "3"),
                questionary.Choice("4) Próxima fecha", "4"),
                questionary.Choice("5) Eliminar fecha", "5"),
                questionary.Choice("0) Salir", "0"),
            ],
            style=questionary.Style([
                ('qmark', 'fg:#673ab7 bold'),       # token in front of the question
                ('question', 'bold'),               # question text
                ('ans', 'fg:#f44336 bold'),         # submitted answer text behind the question
                ('pointer', 'fg:#673ab7 bold'),     # pointer used in select and checkbox prompts
                ('highlighted', 'fg:#673ab7 bold'), # pointed-at choice in select and checkbox prompts
                ('selected', 'fg:#cc21d2'),         # selected choice in checkbox prompts
            ])
        ).ask()

        if choice == "0" or choice is None:  # Si quiere salir
            console.print("[bold yellow]Hasta luego.[/bold yellow]")  # Mensaje de salida
            return  # Termina la funcion
        if choice == "1":  # Si quiere agregar
            _add_date(service)  # Ejecuta la accion
            _pause()  # Pausa para leer
        elif choice == "2":  # Si quiere ver todas
            _list_dates(service, include_past=True)  # Lista todo
            _pause()  # Pausa para leer
        elif choice == "3":  # Si quiere ver proximas
            _list_dates(service, include_past=False)  # Lista futuras
            _pause()  # Pausa para leer
        elif choice == "4":  # Si quiere la proxima
            _show_next(service)  # Muestra la mas cercana
            _pause()  # Pausa para leer
        elif choice == "5":  # Si quiere eliminar
            _remove_date(service)  # Ejecuta la accion
            _pause()  # Pausa para leer


def _add_date(service: DateCounterService) -> None:  # Agrega una fecha
    """Solicita datos y agrega una nueva fecha."""  # Resume la funcion
    name = questionary.text(
        "Nombre de la fecha:",
        validate=lambda text: True if len(text.strip()) > 0 else "El nombre no puede estar vacío"
    ).ask()
    
    if name is None: return

    date_mode = questionary.select(
        "¿Cómo quieres ingresar la fecha?",
        choices=[
            questionary.Choice("Seleccionar con listas (tipo calendario)", "guided"),
            questionary.Choice("Escribir manualmente", "manual"),
        ]
    ).ask()

    if date_mode is None:
        return

    if date_mode == "guided":
        selected_datetime = _ask_date_with_lists(date.today())
        if selected_datetime is None:
            return
    else:
        date_raw = questionary.text(
            "Fecha (YYYY-MM-DD [HH:MM]):",
            validate=lambda text: True if re.match(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?$", text) else "Formato inválido. Use YYYY-MM-DD o YYYY-MM-DD HH:MM"
        ).ask()

        if date_raw is None:
            return
        selected_datetime = parse_datetime(date_raw)

    description = questionary.text("Descripción (opcional):").ask()
    if description == "": description = None

    try:  # Intenta crear la fecha
        item = ImportantDate(name=name, date=selected_datetime, description=description)  # Crea el objeto
        service.add_date(item)  # Guarda el objeto
        console.print(f"[bold green]✓ Fecha '{name}' agregada correctamente.[/bold green]")
    except ValueError as exc:  # Si algo falla
        console.print(f"[bold red]Error: {exc}[/bold red]")  # Muestra el error


def _list_dates(service: DateCounterService, include_past: bool) -> None:  # Lista fechas
    """Lista fechas y muestra su diferencia con hoy."""  # Resume la funcion
    items = service.list_dates()  # Carga las fechas
    today = date.today()  # Toma el dia actual

    if not include_past:  # Si no quiere ver pasadas
        items = [item for item in items if _coerce_to_date(item.date) >= today]  # Filtra futuras

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
        console.print("[yellow]No hay fechas registradas.[/yellow]")  # Mensaje simple
        return  # Sale de la funcion

    choices = [f"{i+1}) {item.name} ({item.date})" for i, item in enumerate(items)]
    selection = questionary.select(
        "Selecciona la fecha a eliminar (o pulsa Esc para cancelar):",
        choices=choices
    ).ask()

    if selection is None:
        console.print("[yellow]Operación cancelada.[/yellow]")
        return

    index = int(selection.split(')')[0]) - 1
    selected_name = items[index].name

    confirm = questionary.confirm(f"¿Seguro que quieres eliminar '{selected_name}'?", default=False).ask()
    if not confirm:  # Si no confirma
        console.print("[yellow]Operación cancelada.[/yellow]")  # Mensaje de cancelacion
        return  # Sale de la funcion

    removed = service.remove_date(selected_name)  # Intenta eliminar
    if removed:  # Si se elimino
        console.print(f"[bold green]✓ Fecha eliminada: {selected_name}[/bold green]")  # Mensaje ok
    else:  # Si no se encontro
        console.print("[bold red]No se encontró la fecha.[/bold red]")  # Mensaje de error


def _print_items(items: Iterable[ImportantDate], today: date) -> None:  # Imprime la tabla
    """Imprime fechas con detalle usando Rich."""  # Resume la funcion
    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("N", justify="right", style="dim")
    table.add_column("Nombre", style="bold cyan")
    table.add_column("Fecha", justify="center")
    table.add_column("Progreso", ratio=1)

    for index, item in enumerate(items, start=1):  # Recorre las fechas
        event_date = _coerce_to_date(item.date)
        days_delta = (event_date - today).days  # Dias que faltan
        total_days = (event_date - item.created_at).days  # Dias totales desde creacion
        if total_days <= 0:  # Evita division por cero
            total_days = 1  # Usa un valor minimo

        elapsed_days = total_days - days_delta  # Dias transcurridos
        progress_percent = (elapsed_days / total_days) * 100  # Porcentaje de avance
        progress_percent = max(min(progress_percent, 100.0), 0.0)  # Limita el rango

        # Determinar color segun progreso o si vencio
        if days_delta < 0:
            color = "red"
            text_status = f"{abs(days_delta)}d vencido"
        elif days_delta == 0:
            color = "green"
            text_status = "HOY"
        else:
            if progress_percent >= 66: color = "green"
            elif progress_percent >= 33: color = "yellow"
            else: color = "cyan"
            text_status = f"{days_delta}d restantes"

        # Crear barra de progreso Rich
        progress_bar = ProgressBar(
            total=100,
            completed=progress_percent,
            width=20,
            pulse=False,
            style="white on black",
            complete_style=color
        )
        
        progress_text = Text.assemble(
            (f"{progress_percent:5.1f}% ", color),
            text_status
        )
        
        # Combinar barra y texto
        progress_render = Text.assemble(
            f"[{'#' * round(progress_percent/5)}{'-' * (20 - round(progress_percent/5))}] ",
            progress_text
        )
        
        # Enriquecer la fila
        table.add_row(
            str(index),
            item.name,
            item.date.strftime("%Y-%m-%d"),
            progress_render
        )

    console.print(table)


def _clear_screen() -> None:  # Limpia la consola
    """Limpia la pantalla en Windows o Unix."""  # Resume la funcion
    os.system("cls" if os.name == "nt" else "clear")  # Ejecuta el comando correcto


def _pause() -> None:  # Pausa la pantalla
    """Pausa para que el usuario lea la salida."""  # Resume la funcion
    console.print("\n[dim italic]Presiona Enter para continuar...[/dim italic]")
    input()


def _red(text: object) -> str: return str(text) # Obsoleto pero mantengo firma por si acaso
def _green(text: object) -> str: return str(text)
def _yellow(text: object) -> str: return str(text)
def _cyan(text: object) -> str: return str(text)
def _strip_ansi(text: str) -> str: return text
def _pad_ansi(text: str, width: int) -> str: return text
