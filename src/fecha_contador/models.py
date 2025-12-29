"""Modelos de datos y utilidades de parsing."""  # Explica el contenido del modulo

from __future__ import annotations  # Permite tipos adelantados

from dataclasses import dataclass, field  # Herramientas para clases de datos
from datetime import date, datetime  # Tipos de fecha y hora
from typing import Any, Dict, Optional  # Tipos para anotaciones

DATE_FORMAT = "%Y-%m-%d"  # Formato de fecha esperado
DATETIME_FORMAT = "%Y-%m-%d %H:%M"  # Formato de fecha y hora esperado


def parse_date(value: str) -> date:  # Convierte texto a fecha
    """Convierte un string YYYY-MM-DD a un objeto date."""  # Resume la funcion
    try:  # Intenta parsear la fecha
        return datetime.strptime(value, DATE_FORMAT).date()  # Parseo exacto
    except ValueError as exc:  # Captura error de formato
        raise ValueError(f"Formato invalido '{value}'. Se espera YYYY-MM-DD.") from exc  # Mensaje claro


def parse_datetime(value: str) -> datetime:  # Convierte texto a datetime
    """Convierte un string a datetime, soportando solo fecha o fecha y hora."""
    try:
        return datetime.strptime(value, DATETIME_FORMAT)
    except ValueError:
        try:
            # Intenta parsear como fecha y asume medianoche
            return datetime.combine(parse_date(value), datetime.min.time())
        except ValueError as exc:
            raise ValueError(f"Formato invalido '{value}'. Se espera YYYY-MM-DD o YYYY-MM-DD HH:MM.") from exc


@dataclass(frozen=True)  # Hace la clase inmutable
class Category:  # Categoria de fechas
    """Representa una categoria con un color asociado."""  # Resume la clase

    name: str  # Nombre de la categoria
    color: str = "cyan"  # Color para mostrar en UI

    def __post_init__(self) -> None:  # Valida datos al crear
        """Valida los datos despues de crear la instancia."""
        if not self.name or not self.name.strip():
            raise ValueError("El nombre de la categoria no puede estar vacio.")
        if not self.color or not str(self.color).strip():
            raise ValueError("El color de la categoria no puede estar vacio.")

    def to_dict(self) -> Dict[str, Any]:  # Convierte a diccionario
        """Devuelve un dict listo para guardar en JSON."""
        return {
            "name": self.name,
            "color": self.color,
        }

    @staticmethod  # Metodo que no usa self
    def from_dict(payload: Dict[str, Any]) -> "Category":  # Crea desde dict
        """Crea una instancia valida desde un dict."""
        return Category(
            name=payload["name"],
            color=payload.get("color", "cyan"),
        )


@dataclass(frozen=True)  # Hace la clase inmutable
class ImportantDate:  # Modelo principal de fecha
    """Representa una fecha importante con datos basicos."""  # Resume la clase

    name: str  # Nombre de la fecha
    date: datetime  # Fecha y hora del evento
    description: Optional[str] = None  # Texto opcional
    group: str = "General"  # Grupo de la fecha
    created_at: datetime = field(default_factory=datetime.now)  # Fecha de creacion

    def __post_init__(self) -> None:  # Valida datos al crear
        """Valida los datos despues de crear la instancia."""  # Resume la validacion
        if not self.name or not self.name.strip():  # Verifica nombre no vacio
            raise ValueError("El nombre no puede estar vacio.")  # Error si falta nombre

    def to_dict(self) -> Dict[str, Any]:  # Convierte a diccionario
        """Devuelve un dict listo para guardar en JSON."""  # Resume la salida
        return {  # Construye el dict
            "name": self.name,  # Guarda el nombre
            "date": self.date.strftime(DATETIME_FORMAT),  # Guarda la fecha y hora
            "description": self.description,  # Guarda la descripcion
            "group": self.group,  # Guarda el grupo
            "created_at": self.created_at.strftime(DATETIME_FORMAT),  # Guarda la creacion
        }  # Cierra el dict

    @staticmethod  # Metodo que no usa self
    def from_dict(payload: Dict[str, Any]) -> "ImportantDate":  # Crea desde dict
        """Crea una instancia valida desde un dict."""  # Resume el objetivo
        return ImportantDate(  # Crea el objeto
            name=payload["name"],  # Toma el nombre
            date=parse_datetime(payload["date"]),  # Toma la fecha y hora
            description=payload.get("description"),  # Toma la descripcion
            group=payload.get("group") or "General",  # Toma el grupo o usa default
            created_at=_parse_created_at(payload.get("created_at")),  # Toma creacion
        )  # Cierra la creacion


def _parse_created_at(value: Optional[str]) -> datetime:
    if not value:
        return datetime.now()
    if " " in value:
        return parse_datetime(value)
    return datetime.combine(parse_date(value), datetime.min.time())
