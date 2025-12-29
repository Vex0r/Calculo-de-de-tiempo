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

DEFAULT_DATA_PATH = Path("data") / "important_dates.json"  # Ruta de datos
CATEGORY_COLORS = [  # Colores disponibles en selector
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
ANSI_COLOR_CODES = {  # Mapa a nombres ANSI de prompt_toolkit
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
console = Console()  # Consola global de rich


def _coerce_to_date(value: date | datetime) -> date:
    """Normaliza datetime o date a date para comparar por dia."""
    return value.date() if isinstance(value, datetime) else value  # Normaliza tipo


def _ask_date_with_lists(today: date) -> Optional[datetime]:
    """Permite seleccionar una fecha guiada por listas."""
    current_year = today.year  # Año base para la lista
    year_choices = [  # Opciones de año comunes
        questionary.Choice(f"{current_year}", current_year),
        questionary.Choice(f"{current_year + 1}", current_year + 1),
        questionary.Choice(f"{current_year + 2}", current_year + 2),
        questionary.Choice("Otro año...", "custom"),
    ]
    selected_year = questionary.select("Selecciona el año:", choices=year_choices).ask()  # Elige año
    if selected_year is None:
        return None
    if selected_year == "custom":
        custom_year = questionary.text(  # Pide año manual
            "Escribe el año (YYYY):",
            validate=lambda text: True if re.match(r"^\d{4}$", text) else "Año invalido",
        ).ask()
        if custom_year is None:
            return None
        selected_year = int(custom_year)  # Convierte a entero

    month_names = [  # Nombres de meses en orden
        "01 - Enero", "02 - Febrero", "03 - Marzo", "04 - Abril",
        "05 - Mayo", "06 - Junio", "07 - Julio", "08 - Agosto",
        "09 - Septiembre", "10 - Octubre", "11 - Noviembre", "12 - Diciembre",
    ]
    month_choice = questionary.select(  # Seleccion de mes
        "Selecciona el mes:",
        choices=[questionary.Choice(name, index + 1) for index, name in enumerate(month_names)],
    ).ask()
    if month_choice is None:
        return None

    days_in_month = monthrange(int(selected_year), int(month_choice))[1]  # Dias del mes
    weekday_names = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]  # Abreviaturas
    day_choices = []  # Lista de dias disponibles
    for day in range(1, days_in_month + 1):
        weekday = weekday_names[datetime(int(selected_year), int(month_choice), day).weekday()]  # Dia de semana
        day_choices.append(questionary.Choice(f"{day:02d} ({weekday})", day))  # Opcion formateada

    selected_day = questionary.select("Selecciona el dia:", choices=day_choices).ask()  # Elige dia
    if selected_day is None:
        return None

    add_time = questionary.confirm("¿Quieres agregar hora/minuto?", default=False).ask()  # Pregunta hora
    hour = minute = 0  # Valores por defecto
    if add_time:
        hour = _select_time_unit("Hora (HH):", 0, 23, default=12)  # Selector de hora
        if hour is None:
            return None
        minute = _select_time_unit("Minuto (MM):", 0, 59, default=0)  # Selector de minuto
        if minute is None:
            return None
        console.print(f"[bold cyan]Hora seleccionada:[/bold cyan] [white]{hour:02d}:{minute:02d}[/white]")  # Muestra seleccion

    return datetime(int(selected_year), int(month_choice), int(selected_day), hour, minute)  # Construye datetime


def _get_category_map(service: DateCounterService) -> Dict[str, str]:
    categories = service.list_categories()  # Carga categorias
    return {category.name: category.color for category in categories}  # Mapa nombre->color


def _select_color(default: str = "cyan") -> Optional[str]:
    choices = [questionary.Choice(_color_choice_label(color), color) for color in CATEGORY_COLORS]  # Lista con swatch
    choices.append(questionary.Choice("Otro...", "custom"))  # Opcion libre
    selected = questionary.select("Selecciona un color:", choices=choices, default=default).ask()  # Elige color
    if selected is None:
        return None
    if selected == "custom":
        custom_color = questionary.text("Escribe el color (nombre o hex):").ask()  # Entrada libre
        if not custom_color:
            return None
        return custom_color.strip()  # Limpia espacios
    return selected  # Devuelve color elegido


def _select_time_unit(label: str, start: int, end: int, default: int) -> Optional[int]:
    choices = [questionary.Choice(f"{value:02d}", value) for value in range(start, end + 1)]  # Opciones con cero
    selected = questionary.select(label, choices=choices, default=default).ask()  # Selector
    return selected  # Devuelve valor o None


def _color_choice_label(color: str) -> List[Tuple[str, str]]:
    style = ANSI_COLOR_CODES.get(color)  # Busca estilo ANSI
    if style is None:
        return [("", color)]  # Sin estilo, muestra texto plano
    return [("", f"{color} "), (f"fg:{style}", "██")]  # Texto + recuadro


def _select_category(service: DateCounterService, allow_new: bool = True) -> Optional[str]:
    categories = service.list_categories()  # Carga categorias disponibles
    choices = [questionary.Choice(category.name, category.name) for category in categories]  # Opciones
    if allow_new:
        choices.append(questionary.Choice("Nueva categoria...", "__new__"))  # Opcion de alta
    selected = questionary.select("Selecciona la categoria:", choices=choices).ask()  # Selector
    if selected is None:
        return None
    if selected == "__new__":
        name = questionary.text(  # Nombre para nueva categoria
            "Nombre de la nueva categoria:",
            validate=lambda text: True if len(text.strip()) > 0 else "El nombre no puede estar vacio",
        ).ask()
        if not name:
            return None
        color = _select_color()  # Color inicial
        if color is None:
            return None
        try:
            service.add_category(name, color)  # Crea categoria
        except CategoryAlreadyExistsError:
            console.print("[yellow]La categoria ya existe, se usara la existente.[/yellow]")
        return name  # Devuelve nueva categoria
    return selected  # Devuelve seleccion existente


def run() -> None:
    """Ejecuta el menu interactivo."""
    service = DateCounterService(JsonStorage(DEFAULT_DATA_PATH))  # Inicializa servicio

    while True:
        _clear_screen()  # Limpia consola para redibujar

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

        choice = questionary.select(  # Menu principal
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

        if choice == "0" or choice is None:  # Salida del menu
            console.print("[bold yellow]Hasta luego.[/bold yellow]")
            return
        if choice == "1":
            _add_date(service)  # Alta de fecha
            _pause()  # Pausa para lectura
        elif choice == "2":
            _list_dates(service, include_past=True)  # Lista completa
            _pause()
        elif choice == "3":
            _list_dates(service, include_past=False)  # Solo futuras
            _pause()
        elif choice == "4":
            _show_next(service)  # Muestra la mas cercana
            _pause()
        elif choice == "5":
            _remove_date(service)  # Elimina fecha
            _pause()
        elif choice == "6":
            _list_by_category(service)  # Navega por categoria
            _pause()
        elif choice == "7":
            _move_date(service)  # Mueve entre categorias
            _pause()
        elif choice == "8":
            _manage_categories(service)  # Administra categorias
            _pause()


def _add_date(service: DateCounterService) -> None:
    """Solicita datos y agrega una nueva fecha."""
    name = questionary.text(  # Nombre de la fecha
        "Nombre de la fecha:",
        validate=lambda text: True if len(text.strip()) > 0 else "El nombre no puede estar vacio",
    ).ask()
    if name is None:
        return

    date_mode = questionary.select(  # Define modo de ingreso
        "¿Como quieres ingresar la fecha?",
        choices=[
            questionary.Choice("Agregar automaticamente", "guided"),
            questionary.Choice("Escribir manualmente", "manual"),
        ],
    ).ask()
    if date_mode is None:
        return

    if date_mode == "guided":
        selected_datetime = _ask_date_with_lists(date.today())  # Selector guiado
        if selected_datetime is None:
            return
    else:
        date_raw = questionary.text(  # Entrada manual
            "Fecha (YYYY-MM-DD [HH:MM]):",
            validate=lambda text: True
            if re.match(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?$", text)
            else "Formato invalido. Use YYYY-MM-DD o YYYY-MM-DD HH:MM",
        ).ask()
        if date_raw is None:
            return
        selected_datetime = parse_datetime(date_raw)  # Convierte a datetime

    description = questionary.text("Descripcion (opcional):").ask()  # Nota opcional
    if description == "":
        description = None  # Normaliza a None

    group = _select_category(service, allow_new=True)  # Selecciona categoria
    if group is None:
        return

    try:
        item = ImportantDate(  # Construye el modelo
            name=name,
            date=selected_datetime,
            description=description,
            group=group,
        )
        service.add_date(item)  # Guarda en almacenamiento
        console.print(f"[bold green]✓ Fecha '{name}' agregada correctamente.[/bold green]")  # Feedback
    except ValueError as exc:
        console.print(f"[bold red]Error: {exc}[/bold red]")  # Muestra error


def _list_dates(service: DateCounterService, include_past: bool) -> None:
    """Lista fechas y muestra su diferencia con hoy."""
    items = service.list_dates()  # Carga fechas
    today = date.today()  # Fecha actual
    if not include_past:
        items = [item for item in items if _coerce_to_date(item.date) >= today]  # Filtra pasadas
    if not items:
        print("No hay fechas para mostrar.")  # Mensaje vacio
        return

    _print_items(items, datetime.now(), today, _get_category_map(service))  # Render de tabla


def _list_by_category(service: DateCounterService) -> None:
    """Permite navegar por categoria."""
    categories = service.list_categories()  # Carga categorias
    if not categories:
        console.print("[yellow]No hay categorias registradas.[/yellow]")
        return

    include_past = questionary.confirm("¿Incluir fechas pasadas?", default=True).ask()  # Filtro pasadas
    if include_past is None:
        return

    choices = [questionary.Choice("Todas", "__all__")]  # Opcion general
    choices.extend(questionary.Choice(category.name, category.name) for category in categories)  # Opciones
    selection = questionary.select("Selecciona una categoria:", choices=choices).ask()  # Seleccion
    if selection is None:
        return

    group = None if selection == "__all__" else selection  # Define filtro
    items = service.list_dates(group=group)  # Carga fechas filtradas
    today = date.today()  # Fecha actual
    if not include_past:
        items = [item for item in items if _coerce_to_date(item.date) >= today]  # Filtra pasadas
    if not items:
        print("No hay fechas para mostrar.")  # Mensaje vacio
        return

    _print_items(items, datetime.now(), today, _get_category_map(service))  # Render de tabla


def _show_next(service: DateCounterService) -> None:
    """Muestra la fecha mas cercana."""
    upcoming = service.next_date()  # Busca la mas cercana
    if upcoming is None:
        print("No hay fechas registradas.")
        return

    now_dt = datetime.now()  # Marca de tiempo actual
    _print_items([upcoming.item], now_dt, now_dt.date(), _get_category_map(service))  # Render de tabla


def _remove_date(service: DateCounterService) -> None:
    """Elimina una fecha por nombre."""
    items = service.list_dates()  # Carga fechas
    if not items:
        console.print("[yellow]No hay fechas registradas.[/yellow]")
        return

    choices = [f"{i+1}) {item.name} ({item.date})" for i, item in enumerate(items)]  # Opciones
    selection = questionary.select(  # Selector de fecha
        "Selecciona la fecha a eliminar (o pulsa Esc para cancelar):",
        choices=choices,
    ).ask()
    if selection is None:
        console.print("[yellow]Operacion cancelada.[/yellow]")
        return

    index = int(selection.split(")")[0]) - 1  # Convierte opcion a indice
    selected_name = items[index].name  # Nombre seleccionado

    confirm = questionary.confirm(f"¿Seguro que quieres eliminar '{selected_name}'?", default=False).ask()  # Confirmacion
    if not confirm:
        console.print("[yellow]Operacion cancelada.[/yellow]")
        return

    removed = service.remove_date(selected_name)  # Ejecuta eliminacion
    if removed:
        console.print(f"[bold green]✓ Fecha eliminada: {selected_name}[/bold green]")
    else:
        console.print("[bold red]No se encontro la fecha.[/bold red]")


def _move_date(service: DateCounterService) -> None:
    """Mueve una fecha a otra categoria."""
    items = service.list_dates()  # Carga fechas
    if not items:
        console.print("[yellow]No hay fechas registradas.[/yellow]")
        return

    choices = [f"{i+1}) {item.name} ({item.group})" for i, item in enumerate(items)]  # Opciones
    selection = questionary.select(  # Selector de fecha
        "Selecciona la fecha a mover:",
        choices=choices,
    ).ask()
    if selection is None:
        console.print("[yellow]Operacion cancelada.[/yellow]")
        return

    index = int(selection.split(")")[0]) - 1  # Convierte opcion a indice
    selected_item = items[index]  # Item seleccionado

    new_group = _select_category(service, allow_new=True)  # Categoria destino
    if new_group is None:
        return

    moved = service.move_to_group(selected_item.name, new_group)  # Ejecuta movimiento
    if moved:
        console.print(
            f"[bold green]✓ Fecha '{selected_item.name}' movida a '{new_group}'.[/bold green]"
        )
    else:
        console.print("[bold red]No se encontro la fecha.[/bold red]")


def _manage_categories(service: DateCounterService) -> None:
    """Permite crear, actualizar o eliminar categorias."""
    action = questionary.select(  # Selector de accion
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
        name = questionary.text(  # Nombre de categoria
            "Nombre de la nueva categoria:",
            validate=lambda text: True if len(text.strip()) > 0 else "El nombre no puede estar vacio",
        ).ask()
        if not name:
            return
        color = _select_color()  # Color inicial
        if color is None:
            return
        try:
            service.add_category(name, color)  # Guarda categoria
            console.print(f"[bold green]✓ Categoria '{name}' creada.[/bold green]")  # Feedback
        except CategoryAlreadyExistsError as exc:
            console.print(f"[bold yellow]{exc}[/bold yellow]")
        return

    if action == "color":
        category = _select_category(service, allow_new=False)  # Selecciona categoria
        if category is None:
            return
        color = _select_color()  # Selecciona color
        if color is None:
            return
        updated = service.update_category_color(category, color)  # Aplica cambio
        if updated:
            console.print(f"[bold green]✓ Color actualizado para '{category}'.[/bold green]")
        else:
            console.print("[bold red]No se encontro la categoria.[/bold red]")
        return

    if action == "remove":
        categories = service.list_categories()  # Lista de categorias
        choices = [questionary.Choice(category.name, category.name) for category in categories]  # Opciones
        selection = questionary.select("Categoria a eliminar:", choices=choices).ask()  # Seleccion
        if selection is None:
            return
        confirm = questionary.confirm(  # Confirmacion
            f"¿Seguro que quieres eliminar '{selection}'?",
            default=False,
        ).ask()
        if not confirm:
            console.print("[yellow]Operacion cancelada.[/yellow]")
            return

        destination = _select_category(service, allow_new=True)  # Categoria destino
        if destination is None:
            return
        try:
            service.remove_category(selection, move_to=destination)  # Ejecuta eliminacion
            console.print(
                f"[bold green]✓ Categoria '{selection}' eliminada. Fechas movidas a '{destination}'.[/bold green]"
            )
        except CategoryProtectedError as exc:
            console.print(f"[bold red]{exc}[/bold red]")
        except CategoryNotFoundError as exc:
            console.print(f"[bold red]{exc}[/bold red]")


def _print_items(
    items: Iterable[ImportantDate],
    now: datetime,
    today: date,
    category_colors: Dict[str, str],
) -> None:
    """Imprime fechas con detalle usando Rich."""
    table = Table(show_header=True, header_style="bold magenta", box=None)  # Tabla sin bordes
    table.add_column("N", justify="right", style="dim")  # Columna indice
    table.add_column("Nombre", style="bold cyan")  # Columna nombre
    table.add_column("Categoria")  # Columna categoria
    table.add_column("Fecha", justify="center")  # Columna fecha
    table.add_column("Progreso", ratio=1)  # Columna progreso

    for index, item in enumerate(items, start=1):  # Renderiza cada fecha
        event_date = _coerce_to_date(item.date)  # Fecha del evento
        days_delta = (event_date - today).days  # Diferencia en dias
        total_seconds = (item.date - item.created_at).total_seconds()  # Duracion total
        if total_seconds <= 0:
            total_seconds = 1.0  # Evita division por cero
        elapsed_seconds = (now - item.created_at).total_seconds()  # Tiempo transcurrido
        progress_percent = (elapsed_seconds / total_seconds) * 100  # Porcentaje real
        progress_percent = max(min(progress_percent, 100.0), 0.0)  # Limita 0-100

        if days_delta < 0:  # Evento pasado
            color = "red"
            text_status = f"{abs(days_delta)}d vencido"
        elif days_delta == 0:
            color = "green"
            text_status = "HOY"
        else:
            if progress_percent >= 66:  # Avance alto
                color = "green"
            elif progress_percent >= 33:  # Avance medio
                color = "yellow"
            else:  # Avance bajo
                color = "cyan"
            text_status = f"{days_delta}d restantes"

        progress_text = Text.assemble(  # Texto con porcentaje y estado
            (f"{progress_percent:5.1f}% ", color),
            text_status,
        )

        bar_width = 20  # Ancho fijo de la barra
        total_units = (progress_percent / 100) * bar_width  # Unidades reales
        full_blocks = int(total_units)  # Bloques completos
        remainder = total_units - full_blocks  # Fraccion restante
        partial_index = int(remainder * 8)  # Indice de bloque parcial
        partial_blocks = ["", "░", "▒", "▓", "█", "█", "█", "█", "█"]  # Escala visual
        partial_block = partial_blocks[partial_index] if full_blocks < bar_width else ""  # Parcial
        empty_len = bar_width - full_blocks - (1 if partial_block else 0)  # Espacios vacios

        bar_text = Text()  # Contenedor de barra
        bar_text.append("[", style="dim")  # Borde izquierdo
        if full_blocks > 0:
            bar_text.append("█" * full_blocks, style=color)  # Relleno completo
        if partial_block:
            bar_text.append(partial_block, style=color)  # Bloque parcial
        if empty_len > 0:
            bar_text.append("░" * empty_len, style="dim")  # Relleno vacio
        bar_text.append("]", style="dim")  # Borde derecho
        progress_render = bar_text + Text(" ") + progress_text  # Barra + texto

        category_color = category_colors.get(item.group, "white")  # Color por categoria
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
    os.system("cls" if os.name == "nt" else "clear")  # Ejecuta comando adecuado


def _pause() -> None:
    """Pausa para que el usuario lea la salida."""
    console.print("\n[dim italic]Presiona Enter para continuar...[/dim italic]")  # Mensaje
    input()  # Espera entrada


def _red(text: object) -> str: return str(text)
def _green(text: object) -> str: return str(text)
def _yellow(text: object) -> str: return str(text)
def _cyan(text: object) -> str: return str(text)
def _strip_ansi(text: str) -> str: return text
def _pad_ansi(text: str, width: int) -> str: return text
