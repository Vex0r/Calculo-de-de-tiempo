"""Logica principal del contador de fechas."""  # Explica el modulo

from __future__ import annotations  # Permite tipos adelantados

from dataclasses import dataclass  # Herramienta para clases simples
from datetime import date  # Tipo de fecha
from typing import List, Optional  # Tipos para listas y opcionales

from .models import ImportantDate  # Modelo principal
from .storage import JsonStorage  # Almacenamiento JSON


class DateAlreadyExistsError(Exception):  # Error de duplicado
    """Error cuando ya existe una fecha con el mismo nombre."""  # Resume el error
    pass  # No agrega comportamiento extra


@dataclass  # Genera init y otros metodos
class UpcomingDate:  # Contenedor de resultado
    """Agrupa una fecha y su diferencia en dias."""  # Resume la clase

    item: ImportantDate  # La fecha registrada
    days_delta: int  # Dias de diferencia con hoy


class DateCounterService:  # Servicio central
    """Opera la carga, la validacion y los calculos."""  # Resume la clase

    def __init__(self, storage: JsonStorage) -> None:  # Recibe el almacenamiento
        self.storage = storage  # Guarda referencia

    def list_dates(self) -> List[ImportantDate]:  # Lista fechas
        """Devuelve todas las fechas ordenadas."""  # Resume la funcion
        items = self.storage.load()  # Carga desde el almacenamiento
        return sorted(items, key=lambda item: item.date)  # Ordena por fecha

    def add_date(self, item: ImportantDate) -> None:  # Agrega una fecha
        """Agrega una nueva fecha si el nombre no existe."""  # Resume la funcion
        items = self.storage.load()  # Carga existentes
        if self._exists(item.name, items):  # Revisa duplicado
            raise DateAlreadyExistsError(f"Ya existe una fecha con el nombre: {item.name}")  # Falla claro

        items.append(item)  # Agrega el nuevo item
        self.storage.save(items)  # Guarda cambios

    def remove_date(self, name: str) -> bool:  # Elimina por nombre
        """Elimina una fecha por nombre y avisa si existia."""  # Resume la funcion
        items = self.storage.load()  # Carga existentes
        remaining = [item for item in items if item.name.lower() != name.lower()]  # Filtra la lista
        if len(remaining) == len(items):  # Si no cambio
            return False  # No se elimino

        self.storage.save(remaining)  # Guarda la lista nueva
        return True  # Si se elimino

    def next_date(self, today: Optional[date] = None) -> Optional[UpcomingDate]:  # Busca la mas cercana
        """Devuelve la fecha mas cercana a hoy."""  # Resume la funcion
        if today is None:  # Si no se paso una fecha
            today = date.today()  # Usa hoy

        upcoming_list = self._calculate_deltas(today)  # Calcula diferencias
        if not upcoming_list:  # Si no hay fechas
            return None  # No hay resultado

        return min(upcoming_list, key=lambda u: abs(u.days_delta))  # Elige la mas cercana

    def _exists(self, name: str, items: List[ImportantDate]) -> bool:  # Comprueba duplicado
        """Verifica si un nombre ya existe sin importar mayusculas."""  # Resume la funcion
        target = name.lower()  # Normaliza el nombre
        return any(existing.name.lower() == target for existing in items)  # Busca coincidencia

    def _calculate_deltas(self, today: date) -> List[UpcomingDate]:  # Calcula diferencias
        """Calcula la diferencia de dias para todas las fechas."""  # Resume la funcion
        items = self.storage.load()  # Carga existentes
        return [  # Construye la lista
            UpcomingDate(item=item, days_delta=(item.date - today).days)  # Calcula diferencia
            for item in items  # Recorre cada item
        ]  # Cierra la lista
