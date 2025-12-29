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
    parser = argparse.ArgumentParser(description="Contador de fechas importantes")  # Parser base
    subparsers = parser.add_subparsers(dest="command", required=True)  # Subcomandos

    add_parser = subparsers.add_parser("add", help="Agrega una fecha")  # Comando add
    add_parser.add_argument("--name", required=True, help="Nombre de la fecha")  # Nombre requerido
    add_parser.add_argument("--date", required=True, help="Fecha YYYY-MM-DD [HH:MM]")  # Fecha requerida
    add_parser.add_argument("--description", help="Descripcion opcional")  # Texto opcional
    add_parser.add_argument("--group", default="General", help="Categoria opcional")  # Categoria

    list_parser = subparsers.add_parser("list", help="Lista las fechas")  # Comando list
    list_parser.add_argument("--all", action="store_true", help="Incluye pasadas")  # Incluye pasadas
    list_parser.add_argument("--group", help="Filtra por categoria")  # Filtro por categoria

    remove_parser = subparsers.add_parser("remove", help="Elimina una fecha")  # Comando remove
    remove_parser.add_argument("--name", required=True, help="Nombre a eliminar")  # Nombre requerido

    move_parser = subparsers.add_parser("move", help="Mueve una fecha de categoria")  # Comando move
    move_parser.add_argument("--name", required=True, help="Nombre de la fecha")  # Fecha a mover
    move_parser.add_argument("--group", required=True, help="Categoria destino")  # Categoria final

    subparsers.add_parser("next", help="Muestra la fecha mas cercana")  # Comando next

    group_parser = subparsers.add_parser("group", help="Administra categorias")  # Comando group
    group_sub = group_parser.add_subparsers(dest="group_command", required=True)  # Subcomandos group
    group_sub.add_parser("list", help="Lista categorias")  # group list

    group_add = group_sub.add_parser("add", help="Agrega categoria")  # group add
    group_add.add_argument("--name", required=True, help="Nombre de la categoria")  # Nombre requerido
    group_add.add_argument("--color", default="cyan", help="Color de la categoria")  # Color inicial

    group_color = group_sub.add_parser("color", help="Cambia el color")  # group color
    group_color.add_argument("--name", required=True, help="Nombre de la categoria")  # Categoria objetivo
    group_color.add_argument("--color", required=True, help="Nuevo color")  # Color nuevo

    group_remove = group_sub.add_parser("remove", help="Elimina categoria")  # group remove
    group_remove.add_argument("--name", required=True, help="Nombre de la categoria")  # Categoria objetivo
    group_remove.add_argument(
        "--move-to",
        default="General",
        help="Categoria donde se moveran sus fechas",
    )

    return parser


def handle_add(service: DateCounterService, args: argparse.Namespace) -> int:
    """Agrega una fecha usando los datos de consola."""
    try:  # Valida datos y crea modelo
        item = ImportantDate(
            name=args.name,
            date=parse_datetime(args.date),
            description=args.description,
            group=args.group,
        )
        service.add_date(item)  # Persiste la fecha
        print(f"Fecha agregada exitosamente: {item.name} en categoria '{item.group}'")  # Feedback
        return 0  # Exito
    except ValueError as exc:  # Errores de formato o validacion
        print(f"Error de validacion: {exc}")
        return 1
    except DateAlreadyExistsError as exc:  # Error por nombre duplicado
        print(f"Error: {exc}")
        return 1


def handle_list(service: DateCounterService, args: argparse.Namespace) -> int:
    """Muestra las fechas guardadas."""
    items = service.list_dates(group=args.group)  # Carga fechas con filtro opcional
    now = datetime.now()  # Marca de tiempo actual
    if not args.all:  # Filtra fechas pasadas si no se pide todo
        items = [item for item in items if item.date >= now]
    if not items:  # Sin resultados
        print("No hay fechas para mostrar.")
        return 0

    print(f"Listado de fechas ({len(items)}):")
    for item in items:  # Muestra cada fecha
        delta = item.date - now  # Diferencia temporal
        status = "faltan" if delta.total_seconds() >= 0 else "pasaron"  # Etiqueta
        print(
            f" - {item.name:<20} | {item.date} | {item.group:<10} | {status} {abs(delta.days)} dias"
        )
        if item.description:
            print(f"   Nota: {item.description}")  # Muestra la nota
    return 0


def handle_remove(service: DateCounterService, args: argparse.Namespace) -> int:
    """Elimina una fecha por nombre."""
    removed = service.remove_date(args.name)  # Intenta eliminar
    if removed:  # Exito
        print(f"Fecha eliminada: {args.name}")
        return 0
    print(f"No se encontro la fecha: {args.name}")  # Fallo
    return 1


def handle_move(service: DateCounterService, args: argparse.Namespace) -> int:
    """Mueve una fecha a otra categoria."""
    moved = service.move_to_group(args.name, args.group)  # Cambia categoria
    if moved:  # Exito
        print(f"Fecha '{args.name}' movida a '{args.group}'.")
        return 0
    print(f"No se encontro la fecha: {args.name}")  # No existe
    return 1


def handle_next(service: DateCounterService, args: argparse.Namespace) -> int:
    """Muestra la fecha mas cercana."""
    upcoming = service.next_date()  # Busca la mas cercana
    if upcoming is None:  # Sin fechas
        print("No hay fechas registradas.")
        return 0

    item = upcoming.item  # Datos de la fecha
    delta = upcoming.delta  # Diferencia temporal
    status = "faltan" if delta.total_seconds() >= 0 else "pasaron"  # Estado
    print("Fecha mas cercana:")
    print(f"   {item.name} ({item.date}) [Categoria: {item.group}]")  # Detalle principal
    print(f"   {status.upper()} {abs(delta.days)} DIAS")  # Resumen
    if item.description:  # Muestra descripcion si existe
        print(f"   --- {item.description} ---")
    return 0


def handle_group(service: DateCounterService, args: argparse.Namespace) -> int:
    """Maneja subcomandos de categoria."""
    if args.group_command == "list":
        categories = service.list_categories()  # Carga categorias
        if not categories:  # Sin categorias
            print("No hay categorias registradas.")
            return 0
        print(f"Categorias ({len(categories)}):")
        for category in categories:  # Muestra cada categoria
            print(f" - {category.name} | color: {category.color}")
        return 0

    if args.group_command == "add":
        try:  # Crea categoria nueva
            service.add_category(args.name, args.color)
            print(f"Categoria agregada: {args.name} (color {args.color})")
            return 0
        except CategoryAlreadyExistsError as exc:  # Categoria duplicada
            print(f"Error: {exc}")
            return 1

    if args.group_command == "color":
        updated = service.update_category_color(args.name, args.color)  # Cambia color
        if updated:  # Exito
            print(f"Categoria '{args.name}' actualizada a color {args.color}.")
            return 0
        print(f"No se encontro la categoria: {args.name}")  # No existe
        return 1

    if args.group_command == "remove":
        try:  # Elimina categoria y mueve fechas
            service.remove_category(args.name, move_to=args.move_to)
            print(f"Categoria '{args.name}' eliminada. Fechas movidas a '{args.move_to}'.")
            return 0
        except CategoryProtectedError as exc:  # No se puede eliminar
            print(f"Error: {exc}")
            return 1
        except CategoryNotFoundError as exc:  # Categoria no existe
            print(f"Error: {exc}")
            return 1

    print("Comando de categoria invalido.")
    return 1


def run(argv: Optional[List[str]] = None) -> int:  # Entrada principal
    """Orquesta la ejecucion del comando elegido."""
    parser = build_parser()  # Construye definicion de comandos
    args = parser.parse_args(argv)  # Lee argumentos de entrada

    storage = JsonStorage(DEFAULT_DATA_PATH)  # Inicializa almacenamiento
    service = DateCounterService(storage)  # Inicializa servicio

    handlers = {  # Enruta comandos a funciones
        "add": handle_add,
        "list": handle_list,
        "remove": handle_remove,
        "move": handle_move,
        "next": handle_next,
        "group": handle_group,
    }

    handler = handlers.get(args.command)  # Busca el manejador
    if handler:  # Ejecuta si existe
        return handler(service, args)

    parser.print_help()  # Muestra ayuda si no coincide
    return 1  # Indica error
