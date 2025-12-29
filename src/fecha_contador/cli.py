"""Interfaz de linea de comandos."""  # Explica el modulo
from __future__ import annotations  # Permite tipos adelantados

import argparse  # Maneja argumentos de consola
from datetime import datetime  # Tipo de fecha y hora
from pathlib import Path  # Maneja rutas
from typing import List, Optional  # Tipos de ayuda

from .models import ImportantDate, parse_datetime  # Importa modelos y parser
from .service import (  # Importa logica
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
    CategoryProtectedError,
    DateAlreadyExistsError,
    DateCounterService,
)
from .storage import JsonStorage  # Importa almacenamiento

DEFAULT_DATA_PATH = Path("data") / "important_dates.json"  # Ruta por defecto


def build_parser() -> argparse.ArgumentParser:  # Crea el parser
    """Configura los comandos y opciones del CLI."""  # Resume la funcion
    parser = argparse.ArgumentParser(description="Contador de fechas importantes")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Agrega una fecha")
    add_parser.add_argument("--name", required=True, help="Nombre de la fecha")
    add_parser.add_argument("--date", required=True, help="Fecha YYYY-MM-DD [HH:MM]")
    add_parser.add_argument("--description", help="Descripcion opcional")
    add_parser.add_argument("--group", default="General", help="Categoria opcional")

    list_parser = subparsers.add_parser("list", help="Lista las fechas")
    list_parser.add_argument("--all", action="store_true", help="Incluye pasadas")
    list_parser.add_argument("--group", help="Filtra por categoria")

    remove_parser = subparsers.add_parser("remove", help="Elimina una fecha")
    remove_parser.add_argument("--name", required=True, help="Nombre a eliminar")

    move_parser = subparsers.add_parser("move", help="Mueve una fecha de categoria")
    move_parser.add_argument("--name", required=True, help="Nombre de la fecha")
    move_parser.add_argument("--group", required=True, help="Categoria destino")

    subparsers.add_parser("next", help="Muestra la fecha mas cercana")

    group_parser = subparsers.add_parser("group", help="Administra categorias")
    group_sub = group_parser.add_subparsers(dest="group_command", required=True)
    group_sub.add_parser("list", help="Lista categorias")

    group_add = group_sub.add_parser("add", help="Agrega categoria")
    group_add.add_argument("--name", required=True, help="Nombre de la categoria")
    group_add.add_argument("--color", default="cyan", help="Color de la categoria")

    group_color = group_sub.add_parser("color", help="Cambia el color")
    group_color.add_argument("--name", required=True, help="Nombre de la categoria")
    group_color.add_argument("--color", required=True, help="Nuevo color")

    group_remove = group_sub.add_parser("remove", help="Elimina categoria")
    group_remove.add_argument("--name", required=True, help="Nombre de la categoria")
    group_remove.add_argument(
        "--move-to",
        default="General",
        help="Categoria donde se moveran sus fechas",
    )

    return parser


def handle_add(service: DateCounterService, args: argparse.Namespace) -> int:
    """Agrega una fecha usando los datos de consola."""
    try:
        item = ImportantDate(
            name=args.name,
            date=parse_datetime(args.date),
            description=args.description,
            group=args.group,
        )
        service.add_date(item)
        print(f"Fecha agregada exitosamente: {item.name} en categoria '{item.group}'")
        return 0
    except ValueError as exc:
        print(f"Error de validacion: {exc}")
        return 1
    except DateAlreadyExistsError as exc:
        print(f"Error: {exc}")
        return 1


def handle_list(service: DateCounterService, args: argparse.Namespace) -> int:
    """Muestra las fechas guardadas."""
    items = service.list_dates(group=args.group)
    now = datetime.now()
    if not args.all:
        items = [item for item in items if item.date >= now]
    if not items:
        print("No hay fechas para mostrar.")
        return 0

    print(f"Listado de fechas ({len(items)}):")
    for item in items:
        delta = item.date - now
        status = "faltan" if delta.total_seconds() >= 0 else "pasaron"
        print(
            f" - {item.name:<20} | {item.date} | {item.group:<10} | {status} {abs(delta.days)} dias"
        )
        if item.description:
            print(f"   Nota: {item.description}")
    return 0


def handle_remove(service: DateCounterService, args: argparse.Namespace) -> int:
    """Elimina una fecha por nombre."""
    removed = service.remove_date(args.name)
    if removed:
        print(f"Fecha eliminada: {args.name}")
        return 0
    print(f"No se encontro la fecha: {args.name}")
    return 1


def handle_move(service: DateCounterService, args: argparse.Namespace) -> int:
    """Mueve una fecha a otra categoria."""
    moved = service.move_to_group(args.name, args.group)
    if moved:
        print(f"Fecha '{args.name}' movida a '{args.group}'.")
        return 0
    print(f"No se encontro la fecha: {args.name}")
    return 1


def handle_next(service: DateCounterService, args: argparse.Namespace) -> int:
    """Muestra la fecha mas cercana."""
    upcoming = service.next_date()
    if upcoming is None:
        print("No hay fechas registradas.")
        return 0

    item = upcoming.item
    delta = upcoming.delta
    status = "faltan" if delta.total_seconds() >= 0 else "pasaron"
    print("Fecha mas cercana:")
    print(f"   {item.name} ({item.date}) [Categoria: {item.group}]")
    print(f"   {status.upper()} {abs(delta.days)} DIAS")
    if item.description:
        print(f"   --- {item.description} ---")
    return 0


def handle_group(service: DateCounterService, args: argparse.Namespace) -> int:
    """Maneja subcomandos de categoria."""
    if args.group_command == "list":
        categories = service.list_categories()
        if not categories:
            print("No hay categorias registradas.")
            return 0
        print(f"Categorias ({len(categories)}):")
        for category in categories:
            print(f" - {category.name} | color: {category.color}")
        return 0

    if args.group_command == "add":
        try:
            service.add_category(args.name, args.color)
            print(f"Categoria agregada: {args.name} (color {args.color})")
            return 0
        except CategoryAlreadyExistsError as exc:
            print(f"Error: {exc}")
            return 1

    if args.group_command == "color":
        updated = service.update_category_color(args.name, args.color)
        if updated:
            print(f"Categoria '{args.name}' actualizada a color {args.color}.")
            return 0
        print(f"No se encontro la categoria: {args.name}")
        return 1

    if args.group_command == "remove":
        try:
            service.remove_category(args.name, move_to=args.move_to)
            print(f"Categoria '{args.name}' eliminada. Fechas movidas a '{args.move_to}'.")
            return 0
        except CategoryProtectedError as exc:
            print(f"Error: {exc}")
            return 1
        except CategoryNotFoundError as exc:
            print(f"Error: {exc}")
            return 1

    print("Comando de categoria invalido.")
    return 1


def run(argv: Optional[List[str]] = None) -> int:  # Entrada principal
    """Orquesta la ejecucion del comando elegido."""
    parser = build_parser()
    args = parser.parse_args(argv)

    storage = JsonStorage(DEFAULT_DATA_PATH)
    service = DateCounterService(storage)

    handlers = {
        "add": handle_add,
        "list": handle_list,
        "remove": handle_remove,
        "move": handle_move,
        "next": handle_next,
        "group": handle_group,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(service, args)

    parser.print_help()
    return 1
