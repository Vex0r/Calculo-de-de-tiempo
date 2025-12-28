"""Modelos de datos y utilidades de parsing."""  # Explica el contenido del modulo

from __future__ import annotations  # Permite tipos adelantados

from dataclasses import dataclass, field  # Herramientas para clases de datos
from datetime import date, datetime  # Tipos de fecha y hora
from typing import Any, Dict, Optional  # Tipos para anotaciones

DATE_FORMAT = "%Y-%m-%d"  # Formato de fecha esperado


def parse_date(value: str) -> date:  # Convierte texto a fecha
    """Convierte un string YYYY-MM-DD a un objeto date."""  # Resume la funcion
    try:  # Intenta parsear la fecha
        return datetime.strptime(value, DATE_FORMAT).date()  # Parseo exacto
    except ValueError as exc:  # Captura error de formato
        raise ValueError(f"Formato invalido '{value}'. Se espera YYYY-MM-DD.") from exc  # Mensaje claro


@dataclass(frozen=True)  # Hace la clase inmutable
class ImportantDate:  # Modelo principal de fecha
    """Representa una fecha importante con datos basicos."""  # Resume la clase

    name: str  # Nombre de la fecha
    date: date  # Fecha del evento
    description: Optional[str] = None  # Texto opcional
    created_at: date = field(default_factory=date.today)  # Fecha de creacion

    def __post_init__(self) -> None:  # Valida datos al crear
        """Valida los datos despues de crear la instancia."""  # Resume la validacion
        if not self.name or not self.name.strip():  # Verifica nombre no vacio
            raise ValueError("El nombre no puede estar vacio.")  # Error si falta nombre

    def to_dict(self) -> Dict[str, Any]:  # Convierte a diccionario
        """Devuelve un dict listo para guardar en JSON."""  # Resume la salida
        return {  # Construye el dict
            "name": self.name,  # Guarda el nombre
            "date": self.date.strftime(DATE_FORMAT),  # Guarda la fecha
            "description": self.description,  # Guarda la descripcion
            "created_at": self.created_at.strftime(DATE_FORMAT),  # Guarda la creacion
        }  # Cierra el dict

    @staticmethod  # Metodo que no usa self
    def from_dict(payload: Dict[str, Any]) -> "ImportantDate":  # Crea desde dict
        """Crea una instancia valida desde un dict."""  # Resume el objetivo
        return ImportantDate(  # Crea el objeto
            name=payload["name"],  # Toma el nombre
            date=parse_date(payload["date"]),  # Toma la fecha
            description=payload.get("description"),  # Toma la descripcion
            created_at=parse_date(payload["created_at"]) if payload.get("created_at") else date.today(),  # Toma creacion
        )  # Cierra la creacion
