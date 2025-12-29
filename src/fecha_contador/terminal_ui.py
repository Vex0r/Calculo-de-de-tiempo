"""Interfaz interactiva en consola."""  # Explica el modulo
from __future__ import annotations  # Permite tipos adelantados

import os  # Limpia pantalla segun el sistema
import re  # Ayuda a validar entradas
from calendar import monthrange  # Dias por mes
from datetime import date, datetime  # Tipos de fecha y hora
from pathlib import Path  # Maneja rutas
from typing import Dict, Iterable, List, Optional, Tuple  # Tipo para listas simples

import questionary  # Prompts interactivos
from rich.align import Align  # Alineacion
from rich.console import Console  # Consola rica
from rich.panel import Panel  # Paneles para decoracion
from rich.table import Table  # Tablas ricas
from rich.text import Text  # Texto rico

from .models import ImportantDate, parse_datetime  # Importa modelo y parser
from .service import (
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
    CategoryProtectedError,
    DateCounterService,
)
from .storage import JsonStorage  # Importa guardado en disco

DEFAULT_DATA_PATH = Path("data") / "important_dates.json"
CATEGORY_COLORS = [
    "cyan",
    "green",
    "yellow",
    "red",
    "magenta",
    "blue",
    "white",
    "bright_cyan",
    "bright_green",
    "bright_yellow",
    "bright_red",
    "bright_magenta",
    "bright_blue",
]
ANSI_COLOR_CODES = {
    "black": "ansiblack",
    "red": "ansired",
    "green": "ansigreen",
    "yellow": "ansiyellow",
    "blue": "ansiblue",
    "magenta": "ansimagenta",
    "cyan": "ansicyan",
    "white": "ansiwhite",
    "bright_black": "ansibrightblack",
    "bright_red": "ansibrightred",
    "bright_green": "ansibrightgreen",
    "bright_yellow": "ansibrightyellow",
    "bright_blue": "ansibrightblue",
    "bright_magenta": "ansibrightmagenta",
    "bright_cyan": "ansibrightcyan",
    "bright_white": "ansiwhite",
}
console = Console()


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
            validate=lambda text: True if re.match(r"^\d{4}$", text) else "Año invalido",
        ).ask()
        if custom_year is None:
            return None
        selected_year = int(custom_year)

    month_names = [
        "01 - Enero", "02 - Febrero", "03 - Marzo", "04 - Abril",
        "05 - Mayo", "06 - Junio", "07 - Julio", "08 - Agosto",
        "09 - Septiembre", "10 - Octubre", "11 - Noviembre", "12 - Diciembre",
    ]
    month_choice = questionary.select(
        "Selecciona el mes:",
        choices=[questionary.Choice(name, index + 1) for index, name in enumerate(month_names)],
    ).ask()
    if month_choice is None:
        return None

    days_in_month = monthrange(int(selected_year), int(month_choice))[1]
    weekday_names = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    day_choices = []
    for day in range(1, days_in_month + 1):
        weekday = weekday_names[datetime(int(selected_year), int(month_choice), day).weekday()]
        day_choices.append(questionary.Choice(f"{day:02d} ({weekday})", day))

    selected_day = questionary.select("Selecciona el dia:", choices=day_choices).ask()
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


def _get_category_map(service: DateCounterService) -> Dict[str, str]:
    categories = service.list_categories()
    return {category.name: category.color for category in categories}


def _select_color(default: str = "cyan") -> Optional[str]:
    choices = [questionary.Choice(_color_choice_label(color), color) for color in CATEGORY_COLORS]
    choices.append(questionary.Choice("Otro...", "custom"))
    selected = questionary.select("Selecciona un color:", choices=choices, default=default).ask()
    if selected is None:
        return None
    if selected == "custom":
        custom_color = questionary.text("Escribe el color (nombre o hex):").ask()
        if not custom_color:
            return None
        return custom_color.strip()
    return selected


def _color_choice_label(color: str) -> List[Tuple[str, str]]:
    style = ANSI_COLOR_CODES.get(color)
    if style is None:
        return [("", color)]
    return [("", f"{color} "), (f"fg:{style}", "██")]


def _select_category(service: DateCounterService, allow_new: bool = True) -> Optional[str]:
    categories = service.list_categories()
    choices = [questionary.Choice(category.name, category.name) for category in categories]
    if allow_new:
        choices.append(questionary.Choice("Nueva categoria...", "__new__"))
    selected = questionary.select("Selecciona la categoria:", choices=choices).ask()
    if selected is None:
        return None
    if selected == "__new__":
        name = questionary.text(
            "Nombre de la nueva categoria:",
            validate=lambda text: True if len(text.strip()) > 0 else "El nombre no puede estar vacio",
        ).ask()
        if not name:
            return None
        color = _select_color()
        if color is None:
            return None
        try:
            service.add_category(name, color)
        except CategoryAlreadyExistsError:
            console.print("[yellow]La categoria ya existe, se usara la existente.[/yellow]")
        return name
    return selected


def run() -> None:
    """Ejecuta el menu interactivo."""
    service = DateCounterService(JsonStorage(DEFAULT_DATA_PATH))

    while True:
        _clear_screen()

        console.print(
            Panel(
                Align.center(
                    "[bold cyan]CONTADOR PARA FECHAS IMPORTANTES[/bold cyan]",
                    vertical="middle",
                ),
                subtitle="[italic]Cuanto tiempo falta para cada fecha?[/italic]",
                padding=(1, 2),
            )
        )

        choice = questionary.select(
            "¿Que deseas hacer?",
            choices=[
                questionary.Choice("1) Agregar fecha", "1"),
                questionary.Choice("2) Ver fechas agregadas", "2"),
                questionary.Choice("3) Ver proximas", "3"),
                questionary.Choice("4) Proxima fecha", "4"),
                questionary.Choice("5) Eliminar fecha", "5"),
                questionary.Choice("6) Ver por categoria", "6"),
                questionary.Choice("7) Mover fecha de categoria", "7"),
                questionary.Choice("8) Gestionar categorias", "8"),
                questionary.Choice("0) Salir", "0"),
            ],
            style=questionary.Style(
                [
                    ("qmark", "fg:#673ab7 bold"),
                    ("question", "bold"),
                    ("ans", "fg:#f44336 bold"),
                    ("pointer", "fg:#673ab7 bold"),
                    ("highlighted", "fg:#673ab7 bold"),
                    ("selected", "fg:#cc21d2"),
                ]
            ),
        ).ask()

        if choice == "0" or choice is None:
            console.print("[bold yellow]Hasta luego.[/bold yellow]")
            return
        if choice == "1":
            _add_date(service)
            _pause()
        elif choice == "2":
            _list_dates(service, include_past=True)
            _pause()
        elif choice == "3":
            _list_dates(service, include_past=False)
            _pause()
        elif choice == "4":
            _show_next(service)
            _pause()
        elif choice == "5":
            _remove_date(service)
            _pause()
        elif choice == "6":
            _list_by_category(service)
            _pause()
        elif choice == "7":
            _move_date(service)
            _pause()
        elif choice == "8":
            _manage_categories(service)
            _pause()


def _add_date(service: DateCounterService) -> None:
    """Solicita datos y agrega una nueva fecha."""
    name = questionary.text(
        "Nombre de la fecha:",
        validate=lambda text: True if len(text.strip()) > 0 else "El nombre no puede estar vacio",
    ).ask()
    if name is None:
        return

    date_mode = questionary.select(
        "¿Como quieres ingresar la fecha?",
        choices=[
            questionary.Choice("Agregar automaticamente", "guided"),
            questionary.Choice("Escribir manualmente", "manual"),
        ],
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
            validate=lambda text: True
            if re.match(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?$", text)
            else "Formato invalido. Use YYYY-MM-DD o YYYY-MM-DD HH:MM",
        ).ask()
        if date_raw is None:
            return
        selected_datetime = parse_datetime(date_raw)

    description = questionary.text("Descripcion (opcional):").ask()
    if description == "":
        description = None

    group = _select_category(service, allow_new=True)
    if group is None:
        return

    try:
        item = ImportantDate(
            name=name,
            date=selected_datetime,
            description=description,
            group=group,
        )
        service.add_date(item)
        console.print(f"[bold green]✓ Fecha '{name}' agregada correctamente.[/bold green]")
    except ValueError as exc:
        console.print(f"[bold red]Error: {exc}[/bold red]")


def _list_dates(service: DateCounterService, include_past: bool) -> None:
    """Lista fechas y muestra su diferencia con hoy."""
    items = service.list_dates()
    today = date.today()
    if not include_past:
        items = [item for item in items if _coerce_to_date(item.date) >= today]
    if not items:
        print("No hay fechas para mostrar.")
        return

    _print_items(items, today, _get_category_map(service))


def _list_by_category(service: DateCounterService) -> None:
    """Permite navegar por categoria."""
    categories = service.list_categories()
    if not categories:
        console.print("[yellow]No hay categorias registradas.[/yellow]")
        return

    include_past = questionary.confirm("¿Incluir fechas pasadas?", default=True).ask()
    if include_past is None:
        return

    choices = [questionary.Choice("Todas", "__all__")]
    choices.extend(questionary.Choice(category.name, category.name) for category in categories)
    selection = questionary.select("Selecciona una categoria:", choices=choices).ask()
    if selection is None:
        return

    group = None if selection == "__all__" else selection
    items = service.list_dates(group=group)
    today = date.today()
    if not include_past:
        items = [item for item in items if _coerce_to_date(item.date) >= today]
    if not items:
        print("No hay fechas para mostrar.")
        return

    _print_items(items, today, _get_category_map(service))


def _show_next(service: DateCounterService) -> None:
    """Muestra la fecha mas cercana."""
    upcoming = service.next_date()
    if upcoming is None:
        print("No hay fechas registradas.")
        return

    _print_items([upcoming.item], date.today(), _get_category_map(service))


def _remove_date(service: DateCounterService) -> None:
    """Elimina una fecha por nombre."""
    items = service.list_dates()
    if not items:
        console.print("[yellow]No hay fechas registradas.[/yellow]")
        return

    choices = [f"{i+1}) {item.name} ({item.date})" for i, item in enumerate(items)]
    selection = questionary.select(
        "Selecciona la fecha a eliminar (o pulsa Esc para cancelar):",
        choices=choices,
    ).ask()
    if selection is None:
        console.print("[yellow]Operacion cancelada.[/yellow]")
        return

    index = int(selection.split(")")[0]) - 1
    selected_name = items[index].name

    confirm = questionary.confirm(f"¿Seguro que quieres eliminar '{selected_name}'?", default=False).ask()
    if not confirm:
        console.print("[yellow]Operacion cancelada.[/yellow]")
        return

    removed = service.remove_date(selected_name)
    if removed:
        console.print(f"[bold green]✓ Fecha eliminada: {selected_name}[/bold green]")
    else:
        console.print("[bold red]No se encontro la fecha.[/bold red]")


def _move_date(service: DateCounterService) -> None:
    """Mueve una fecha a otra categoria."""
    items = service.list_dates()
    if not items:
        console.print("[yellow]No hay fechas registradas.[/yellow]")
        return

    choices = [f"{i+1}) {item.name} ({item.group})" for i, item in enumerate(items)]
    selection = questionary.select(
        "Selecciona la fecha a mover:",
        choices=choices,
    ).ask()
    if selection is None:
        console.print("[yellow]Operacion cancelada.[/yellow]")
        return

    index = int(selection.split(")")[0]) - 1
    selected_item = items[index]

    new_group = _select_category(service, allow_new=True)
    if new_group is None:
        return

    moved = service.move_to_group(selected_item.name, new_group)
    if moved:
        console.print(
            f"[bold green]✓ Fecha '{selected_item.name}' movida a '{new_group}'.[/bold green]"
        )
    else:
        console.print("[bold red]No se encontro la fecha.[/bold red]")


def _manage_categories(service: DateCounterService) -> None:
    """Permite crear, actualizar o eliminar categorias."""
    action = questionary.select(
        "Gestion de categorias:",
        choices=[
            questionary.Choice("Crear categoria", "create"),
            questionary.Choice("Cambiar color", "color"),
            questionary.Choice("Eliminar categoria", "remove"),
            questionary.Choice("Volver", "back"),
        ],
    ).ask()
    if action is None or action == "back":
        return

    if action == "create":
        name = questionary.text(
            "Nombre de la nueva categoria:",
            validate=lambda text: True if len(text.strip()) > 0 else "El nombre no puede estar vacio",
        ).ask()
        if not name:
            return
        color = _select_color()
        if color is None:
            return
        try:
            service.add_category(name, color)
            console.print(f"[bold green]✓ Categoria '{name}' creada.[/bold green]")
        except CategoryAlreadyExistsError as exc:
            console.print(f"[bold yellow]{exc}[/bold yellow]")
        return

    if action == "color":
        category = _select_category(service, allow_new=False)
        if category is None:
            return
        color = _select_color()
        if color is None:
            return
        updated = service.update_category_color(category, color)
        if updated:
            console.print(f"[bold green]✓ Color actualizado para '{category}'.[/bold green]")
        else:
            console.print("[bold red]No se encontro la categoria.[/bold red]")
        return

    if action == "remove":
        categories = service.list_categories()
        choices = [questionary.Choice(category.name, category.name) for category in categories]
        selection = questionary.select("Categoria a eliminar:", choices=choices).ask()
        if selection is None:
            return
        confirm = questionary.confirm(
            f"¿Seguro que quieres eliminar '{selection}'?",
            default=False,
        ).ask()
        if not confirm:
            console.print("[yellow]Operacion cancelada.[/yellow]")
            return

        destination = _select_category(service, allow_new=True)
        if destination is None:
            return
        try:
            service.remove_category(selection, move_to=destination)
            console.print(
                f"[bold green]✓ Categoria '{selection}' eliminada. Fechas movidas a '{destination}'.[/bold green]"
            )
        except CategoryProtectedError as exc:
            console.print(f"[bold red]{exc}[/bold red]")
        except CategoryNotFoundError as exc:
            console.print(f"[bold red]{exc}[/bold red]")


def _print_items(items: Iterable[ImportantDate], today: date, category_colors: Dict[str, str]) -> None:
    """Imprime fechas con detalle usando Rich."""
    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("N", justify="right", style="dim")
    table.add_column("Nombre", style="bold cyan")
    table.add_column("Categoria")
    table.add_column("Fecha", justify="center")
    table.add_column("Progreso", ratio=1)

    for index, item in enumerate(items, start=1):
        event_date = _coerce_to_date(item.date)
        days_delta = (event_date - today).days
        total_days = (event_date - item.created_at).days
        if total_days <= 0:
            total_days = 1

        elapsed_days = total_days - days_delta
        progress_percent = (elapsed_days / total_days) * 100
        progress_percent = max(min(progress_percent, 100.0), 0.0)

        if days_delta < 0:
            color = "red"
            text_status = f"{abs(days_delta)}d vencido"
        elif days_delta == 0:
            color = "green"
            text_status = "HOY"
        else:
            if progress_percent >= 66:
                color = "green"
            elif progress_percent >= 33:
                color = "yellow"
            else:
                color = "cyan"
            text_status = f"{days_delta}d restantes"

        progress_text = Text.assemble(
            (f"{progress_percent:5.1f}% ", color),
            text_status,
        )

        bar_width = 20
        total_units = (progress_percent / 100) * bar_width
        full_blocks = int(total_units)
        remainder = total_units - full_blocks
        partial_index = int(remainder * 8)
        partial_blocks = ["", "░", "▒", "▓", "█", "█", "█", "█", "█"]
        partial_block = partial_blocks[partial_index] if full_blocks < bar_width else ""
        empty_len = bar_width - full_blocks - (1 if partial_block else 0)

        bar_text = Text()
        bar_text.append("[", style="dim")
        if full_blocks > 0:
            bar_text.append("█" * full_blocks, style=color)
        if partial_block:
            bar_text.append(partial_block, style=color)
        if empty_len > 0:
            bar_text.append("░" * empty_len, style="dim")
        bar_text.append("]", style="dim")
        progress_render = bar_text + Text(" ") + progress_text

        category_color = category_colors.get(item.group, "white")
        table.add_row(
            str(index),
            item.name,
            Text(item.group, style=category_color),
            item.date.strftime("%Y-%m-%d"),
            progress_render,
        )

    console.print(table)


def _clear_screen() -> None:
    """Limpia la pantalla en Windows o Unix."""
    os.system("cls" if os.name == "nt" else "clear")


def _pause() -> None:
    """Pausa para que el usuario lea la salida."""
    console.print("\n[dim italic]Presiona Enter para continuar...[/dim italic]")
    input()


def _red(text: object) -> str: return str(text)
def _green(text: object) -> str: return str(text)
def _yellow(text: object) -> str: return str(text)
def _cyan(text: object) -> str: return str(text)
def _strip_ansi(text: str) -> str: return text
def _pad_ansi(text: str, width: int) -> str: return text
