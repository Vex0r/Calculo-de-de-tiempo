"""Logica principal del contador de fechas."""  # Explica el modulo
from __future__ import annotations  # Permite tipos adelantados

from dataclasses import dataclass  # Herramienta para clases simples
from datetime import date, datetime, timedelta  # Tipos de fecha, hora y diferencia
from typing import List, Optional  # Tipos para listas y opcionales

from .models import Category, ImportantDate  # Modelos principales
from .storage import JsonStorage, StoredData  # Almacenamiento JSON


class DateAlreadyExistsError(Exception):  # Error de duplicado
    """Error cuando ya existe una fecha con el mismo nombre."""  # Resume el error


class CategoryAlreadyExistsError(Exception):  # Error de duplicado
    """Error cuando ya existe una categoria con el mismo nombre."""


class CategoryNotFoundError(Exception):  # Error cuando no existe
    """Error cuando no se encuentra una categoria."""


class CategoryProtectedError(Exception):  # Error cuando no se permite
    """Error cuando no se puede eliminar una categoria protegida."""


@dataclass  # Genera init y otros metodos
class UpcomingDate:  # Contenedor de resultado
    """Agrupa una fecha y su diferencia de tiempo."""  # Resume la clase

    item: ImportantDate  # La fecha registrada
    delta: timedelta  # Diferencia de tiempo con el momento de comparacion


class DateCounterService:  # Servicio central
    """Opera la carga, la validacion y los calculos."""  # Resume la clase

    def __init__(self, storage: JsonStorage) -> None:  # Recibe el almacenamiento
        self.storage = storage  # Guarda referencia

    def list_dates(self, group: Optional[str] = None) -> List[ImportantDate]:  # Lista fechas
        """Devuelve todas las fechas ordenadas, opcionalmente filtradas."""
        data = self.storage.load()
        items = data.dates
        if group:
            target = group.lower()
            items = [item for item in items if item.group.lower() == target]
        return sorted(items, key=lambda item: item.date)

    def list_categories(self) -> List[Category]:  # Lista categorias
        """Devuelve todas las categorias ordenadas."""
        data = self.storage.load()
        return sorted(data.categories, key=lambda category: category.name.lower())

    def add_category(self, name: str, color: str) -> None:  # Agrega categoria
        """Agrega una nueva categoria."""
        data = self.storage.load()
        if self._category_exists(name, data.categories):
            raise CategoryAlreadyExistsError(f"Ya existe la categoria: {name}")
        data.categories.append(Category(name=name, color=color))
        self.storage.save(data)

    def update_category_color(self, name: str, color: str) -> bool:  # Cambia color
        """Actualiza el color de una categoria existente."""
        data = self.storage.load()
        updated = False
        new_categories: List[Category] = []
        for category in data.categories:
            if category.name.lower() == name.lower():
                new_categories.append(Category(name=category.name, color=color))
                updated = True
            else:
                new_categories.append(category)
        if updated:
            self.storage.save(StoredData(dates=data.dates, categories=new_categories))
        return updated

    def remove_category(self, name: str, move_to: str = "General") -> None:  # Elimina
        """Elimina una categoria y mueve sus fechas a otra."""
        if name.lower() == "general":
            raise CategoryProtectedError("La categoria 'General' no se puede eliminar.")

        if move_to.lower() == name.lower():
            raise CategoryProtectedError("La categoria destino no puede ser la misma que la eliminada.")

        move_to = self._normalize_group(move_to)
        data = self.storage.load()
        if not self._category_exists(name, data.categories):
            raise CategoryNotFoundError(f"No se encontro la categoria: {name}")

        categories = [category for category in data.categories if category.name.lower() != name.lower()]
        if not self._category_exists(move_to, categories):
            categories.append(Category(name=move_to))

        updated_dates = [
            self._with_group(item, move_to) if item.group.lower() == name.lower() else item
            for item in data.dates
        ]
        self.storage.save(StoredData(dates=updated_dates, categories=categories))

    def add_date(self, item: ImportantDate) -> None:  # Agrega una fecha
        """Agrega una nueva fecha si el nombre no existe."""
        data = self.storage.load()
        if self._exists(item.name, data.dates):
            raise DateAlreadyExistsError(f"Ya existe una fecha con el nombre: {item.name}")

        normalized_group = self._normalize_group(item.group)
        if normalized_group != item.group:
            item = self._with_group(item, normalized_group)
        data.dates.append(item)
        if not self._category_exists(normalized_group, data.categories):
            data.categories.append(Category(name=normalized_group))
        self.storage.save(data)

    def remove_date(self, name: str) -> bool:  # Elimina por nombre
        """Elimina una fecha por nombre y avisa si existia."""
        data = self.storage.load()
        remaining = [item for item in data.dates if item.name.lower() != name.lower()]
        if len(remaining) == len(data.dates):
            return False

        self.storage.save(StoredData(dates=remaining, categories=data.categories))
        return True

    def move_to_group(self, name: str, group_name: str) -> bool:  # Cambia grupo
        """Mueve una fecha a un nuevo grupo."""
        data = self.storage.load()
        found = False
        group_name = self._normalize_group(group_name)
        new_items = []
        for item in data.dates:
            if item.name.lower() == name.lower():
                new_items.append(self._with_group(item, group_name))
                found = True
            else:
                new_items.append(item)

        if found:
            if not self._category_exists(group_name, data.categories):
                data.categories.append(Category(name=group_name))
            self.storage.save(StoredData(dates=new_items, categories=data.categories))
        return found

    def next_date(self, now: Optional[datetime] = None) -> Optional[UpcomingDate]:
        """Devuelve la fecha mas cercana al momento dado."""
        if now is None:
            now = datetime.now()

        upcoming_list = self._calculate_deltas(now)
        if not upcoming_list:
            return None

        return min(upcoming_list, key=lambda u: abs(u.delta.total_seconds()))

    def _exists(self, name: str, items: List[ImportantDate]) -> bool:  # Comprueba duplicado
        """Verifica si un nombre ya existe sin importar mayusculas."""
        target = name.lower()
        return any(existing.name.lower() == target for existing in items)

    def _category_exists(self, name: str, categories: List[Category]) -> bool:
        target = name.lower()
        return any(category.name.lower() == target for category in categories)

    def _with_group(self, item: ImportantDate, group_name: str) -> ImportantDate:
        return ImportantDate(
            name=item.name,
            date=item.date,
            description=item.description,
            group=group_name,
            created_at=item.created_at,
        )

    def _normalize_group(self, group_name: str) -> str:
        if not group_name or not group_name.strip():
            return "General"
        return group_name.strip()

    def _calculate_deltas(self, now: datetime) -> List[UpcomingDate]:  # Calcula diferencias
        """Calcula la diferencia de tiempo para todas las fechas."""
        data = self.storage.load()
        return [
            UpcomingDate(item=item, delta=(item.date - now))
            for item in data.dates
        ]
