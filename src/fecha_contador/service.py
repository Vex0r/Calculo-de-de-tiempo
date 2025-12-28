"""Logica principal del contador de fechas."""  # Explica el modulo

from __future__ import annotations  # Permite tipos adelantados

from dataclasses import dataclass  # Herramienta para clases simples
from datetime import date, datetime, timedelta  # Tipos de fecha, hora y diferencia
from typing import List, Optional  # Tipos para listas y opcionales

from .models import ImportantDate  # Modelo principal
from .storage import JsonStorage  # Almacenamiento JSON


class DateAlreadyExistsError(Exception):  # Error de duplicado
    """Error cuando ya existe una fecha con el mismo nombre."""  # Resume el error
    pass  # No agrega comportamiento extra


@dataclass  # Genera init y otros metodos
class UpcomingDate:  # Contenedor de resultado
    """Agrupa una fecha y su diferencia de tiempo."""  # Resume la clase

    item: ImportantDate  # La fecha registrada
    delta: timedelta  # Diferencia de tiempo con el momento de comparacion


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

    def get_groups(self) -> List[str]:  # Lista todos los grupos
        """Devuelve una lista unica de nombres de grupos."""
        items = self.storage.load()  # Carga existentes
        groups = {item.group for item in items}  # Extrae grupos unicos
        return sorted(list(groups))  # Devuelve ordenados

    def move_to_group(self, name: str, group_name: str) -> bool:  # Cambia grupo
        """Mueve una fecha a un nuevo grupo."""
        items = self.storage.load()  # Carga existentes
        found = False  # Bandera de encontrado
        new_items = []  # Nueva lista

        for item in items:  # Recorre cada item
            if item.name.lower() == name.lower():  # Busca coincidencia
                # Re-crea el item con el nuevo grupo (es inmutable)
                updated = ImportantDate(
                    name=item.name,
                    date=item.date,
                    description=item.description,
                    group=group_name,
                    created_at=item.created_at,
                )
                new_items.append(updated)  # Agrega el actualizado
                found = True  # Marca como encontrado
            else:
                new_items.append(item)  # Agrega el original

        if found:  # Si hubo cambios
            self.storage.save(new_items)  # Guarda cambios
        return found  # Avisa si se encontro

    def next_date(self, now: Optional[datetime] = None) -> Optional[UpcomingDate]:  # Busca la mas cercana
        """Devuelve la fecha mas cercana al momento dado."""  # Resume la funcion
        if now is None:  # Si no se paso una fecha
            now = datetime.now()  # Usa el momento actual

        upcoming_list = self._calculate_deltas(now)  # Calcula diferencias
        if not upcoming_list:  # Si no hay fechas
            return None  # No hay resultado

        # Compara por el valor absoluto del delta total en segundos
        return min(upcoming_list, key=lambda u: abs(u.delta.total_seconds()))

    def _exists(self, name: str, items: List[ImportantDate]) -> bool:  # Comprueba duplicado
        """Verifica si un nombre ya existe sin importar mayusculas."""  # Resume la funcion
        target = name.lower()  # Normaliza el nombre
        return any(existing.name.lower() == target for existing in items)  # Busca coincidencia

    def _calculate_deltas(self, now: datetime) -> List[UpcomingDate]:  # Calcula diferencias
        """Calcula la diferencia de tiempo para todas las fechas."""  # Resume la funcion
        items = self.storage.load()  # Carga existentes
        return [  # Construye la lista
            UpcomingDate(item=item, delta=(item.date - now))  # Calcula diferencia
            for item in items  # Recorre cada item
        ]  # Cierra la lista
