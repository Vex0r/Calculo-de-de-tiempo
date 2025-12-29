"""Persistencia en JSON para las fechas."""  # Explica el modulo
from __future__ import annotations  # Permite tipos adelantados

import json  # Maneja JSON
from dataclasses import dataclass  # Herramientas para clases simples
from pathlib import Path  # Maneja rutas
from typing import Dict, List  # Tipos para listas

from .models import Category, ImportantDate  # Modelos principales


@dataclass
class StoredData:  # Contenedor de datos persistidos
    """Agrupa fechas y categorias cargadas desde JSON."""

    dates: List[ImportantDate]
    categories: List[Category]


class JsonStorage:  # Clase de guardado
    """Carga y guarda fechas importantes en JSON."""  # Resume la clase

    def __init__(self, path: Path) -> None:  # Guarda la ruta del archivo
        self.path = path  # Ruta donde se guarda el JSON

    def load(self) -> StoredData:  # Lee el archivo
        """Lee el archivo y devuelve fechas y categorias validas."""
        if not self.path.exists():  # Si no existe el archivo
            return StoredData(dates=[], categories=[Category(name="General")])

        try:  # Intenta leer el JSON
            with self.path.open("r", encoding="utf-8") as handle:  # Abre el archivo
                raw_payload = json.load(handle)  # Carga el contenido
        except json.JSONDecodeError as exc:  # Captura JSON roto
            raise json.JSONDecodeError(
                f"El archivo {self.path} esta corrupto.", exc.doc, exc.pos
            ) from exc

        dirty = False  # Indica si hubo migraciones
        if isinstance(raw_payload, list):  # Formato antiguo solo con fechas
            raw_dates = raw_payload
            raw_categories: List[Dict[str, object]] = []
            dirty = True
        elif isinstance(raw_payload, dict):
            raw_dates = list(raw_payload.get("dates", []))
            raw_categories = list(raw_payload.get("categories", []))
        else:
            raise ValueError("Formato invalido de almacenamiento.")

        dates: List[ImportantDate] = []
        has_missing_created = any("created_at" not in item for item in raw_dates)
        for item in raw_dates:
            try:
                dates.append(ImportantDate.from_dict(item))
            except (KeyError, ValueError) as exc:
                raise ValueError(f"Item invalido encontrado en el almacenamiento: {item}") from exc

        categories, added_missing = self._load_categories(raw_categories, dates)
        if not raw_categories or added_missing:
            dirty = True
        if has_missing_created:
            dirty = True

        if dirty:
            self.save(StoredData(dates=dates, categories=categories))

        return StoredData(dates=dates, categories=categories)

    def save(self, data: StoredData) -> None:  # Guarda el archivo
        """Guarda fechas y categorias en formato JSON legible."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "dates": [item.to_dict() for item in data.dates],
            "categories": [category.to_dict() for category in data.categories],
        }
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True)

    def _load_categories(
        self, raw_categories: List[Dict[str, object]], dates: List[ImportantDate]
    ) -> tuple[List[Category], bool]:
        categories: Dict[str, Category] = {}
        added_missing = False
        for entry in raw_categories:
            try:
                category = Category.from_dict(entry)
            except (KeyError, ValueError) as exc:
                raise ValueError(f"Categoria invalida en almacenamiento: {entry}") from exc
            categories[category.name.lower()] = category

        for item in dates:
            group_name = item.group or "General"
            if group_name.lower() not in categories:
                categories[group_name.lower()] = Category(name=group_name)
                added_missing = True

        if "general" not in categories:
            categories["general"] = Category(name="General")
            added_missing = True

        return list(categories.values()), added_missing
