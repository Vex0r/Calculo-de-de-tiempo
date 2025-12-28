"""Interfaz de linea de comandos."""  # Explica el modulo

from __future__ import annotations  # Permite tipos adelantados

import argparse  # Maneja argumentos de consola
from datetime import date  # Tipo de fecha
from pathlib import Path  # Maneja rutas
from typing import List, Optional  # Tipos de ayuda

from .models import ImportantDate, parse_date  # Importa modelos
from .service import DateCounterService, DateAlreadyExistsError  # Importa logica
from .storage import JsonStorage  # Importa almacenamiento

DEFAULT_DATA_PATH = Path("data") / "important_dates.json"  # Ruta por defecto


def build_parser() -> argparse.ArgumentParser:  # Crea el parser
    """Configura los comandos y opciones del CLI."""  # Resume la funcion
    parser = argparse.ArgumentParser(description="Contador de fechas importantes")  # Crea parser
    subparsers = parser.add_subparsers(dest="command", required=True)  # Crea subcomandos

    add_parser = subparsers.add_parser("add", help="Agrega una fecha")  # Comando add
    add_parser.add_argument("--name", required=True, help="Nombre de la fecha")  # Nombre
    add_parser.add_argument("--date", required=True, help="Fecha YYYY-MM-DD")  # Fecha
    add_parser.add_argument("--description", help="Descripcion opcional")  # Descripcion

    list_parser = subparsers.add_parser("list", help="Lista las fechas")  # Comando list
    list_parser.add_argument("--all", action="store_true", help="Incluye pasadas")  # Opcion all

    remove_parser = subparsers.add_parser("remove", help="Elimina una fecha")  # Comando remove
    remove_parser.add_argument("--name", required=True, help="Nombre a eliminar")  # Nombre

    subparsers.add_parser("next", help="Muestra la fecha mas cercana")  # Comando next

    return parser  # Devuelve el parser


def handle_add(service: DateCounterService, args: argparse.Namespace) -> int:  # Maneja add
    """Agrega una fecha usando los datos de consola."""  # Resume la funcion
    try:  # Inicia bloque seguro
        item = ImportantDate(  # Crea el objeto
            name=args.name,  # Usa el nombre
            date=parse_date(args.date),  # Convierte la fecha
            description=args.description,  # Usa la descripcion
        )  # Cierra el objeto
        service.add_date(item)  # Guarda en almacenamiento
        print(f"Fecha agregada exitosamente: {item.name}")  # Mensaje al usuario
        return 0  # Indica exito
    except ValueError as exc:  # Captura errores de formato
        print(f"Error de validacion: {exc}")  # Muestra el problema
        return 1  # Indica error
    except DateAlreadyExistsError as exc:  # Captura duplicados
        print(f"Error: {exc}")  # Muestra el problema
        return 1  # Indica error


def handle_list(service: DateCounterService, args: argparse.Namespace) -> int:  # Maneja list
    """Muestra las fechas guardadas."""  # Resume la funcion
    items = service.list_dates()  # Carga las fechas
    today = date.today()  # Toma el dia actual
    if not args.all:  # Si no pidio todas
        items = [item for item in items if item.date >= today]  # Deja solo futuras
    if not items:  # Si no hay datos
        print("No hay fechas para mostrar.")  # Aviso simple
        return 0  # Termina sin error

    print(f"Listado de fechas ({len(items)}):")  # Encabezado
    for item in items:  # Recorre cada fecha
        days_delta = (item.date - today).days  # Calcula diferencia
        status = "faltan" if days_delta >= 0 else "pasaron"  # Decide texto
        print(f" - {item.name:<20} | {item.date} | {status} {abs(days_delta)} dias")  # Muestra fila
        if item.description:  # Si hay descripcion
            print(f"   Nota: {item.description}")  # Muestra nota
    return 0  # Indica exito


def handle_remove(service: DateCounterService, args: argparse.Namespace) -> int:  # Maneja remove
    """Elimina una fecha por nombre."""  # Resume la funcion
    removed = service.remove_date(args.name)  # Intenta borrar
    if removed:  # Si se elimino
        print(f"Fecha eliminada: {args.name}")  # Mensaje ok
        return 0  # Indica exito
    print(f"No se encontro la fecha: {args.name}")  # Mensaje de error
    return 1  # Indica error


def handle_next(service: DateCounterService, args: argparse.Namespace) -> int:  # Maneja next
    """Muestra la fecha mas cercana."""  # Resume la funcion
    upcoming = service.next_date()  # Busca la mas cercana
    if upcoming is None:  # Si no hay datos
        print("No hay fechas registradas.")  # Aviso simple
        return 0  # Termina sin error

    item = upcoming.item  # Toma el item
    days_delta = upcoming.days_delta  # Toma la diferencia
    status = "faltan" if days_delta >= 0 else "pasaron"  # Texto de estado
    print("Fecha mas cercana:")  # Encabezado
    print(f"   {item.name} ({item.date})")  # Muestra nombre y fecha
    print(f"   {status.upper()} {abs(days_delta)} DIAS")  # Muestra resumen
    if item.description:  # Si hay descripcion
        print(f"   --- {item.description} ---")  # Muestra descripcion
    return 0  # Indica exito


def run(argv: Optional[List[str]] = None) -> int:  # Entrada principal
    """Orquesta la ejecucion del comando elegido."""  # Resume la funcion
    parser = build_parser()  # Crea el parser
    args = parser.parse_args(argv)  # Lee argumentos

    storage = JsonStorage(DEFAULT_DATA_PATH)  # Prepara almacenamiento
    service = DateCounterService(storage)  # Prepara servicio

    handlers = {  # Mapa de comandos a funciones
        "add": handle_add,  # Maneja add
        "list": handle_list,  # Maneja list
        "remove": handle_remove,  # Maneja remove
        "next": handle_next,  # Maneja next
    }  # Cierra el mapa

    handler = handlers.get(args.command)  # Busca el manejador
    if handler:  # Si existe
        return handler(service, args)  # Ejecuta y devuelve codigo

    parser.print_help()  # Muestra ayuda si algo falla
    return 1  # Indica error
