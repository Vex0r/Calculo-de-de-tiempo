"""Persistencia en JSON para las fechas."""  # Explica el modulo
from __future__ import annotations  # Permite tipos adelantados

import json  # Maneja JSON
from dataclasses import dataclass  # Herramientas para clases simples
from pathlib import Path  # Maneja rutas
from typing import Dict, List  # Tipos para listas

from .models import Category, ImportantDate  # Modelos principales


@dataclass  # Genera init para el contenedor
class StoredData:  # Contenedor de datos persistidos
    """Agrupa fechas y categorias cargadas desde JSON."""

    dates: List[ImportantDate]  # Lista completa de fechas
    categories: List[Category]  # Lista de categorias disponibles


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

        dirty = False  # Marca si hay que reescribir con esquema nuevo
        if isinstance(raw_payload, list):  # Formato antiguo solo con fechas
            raw_dates = raw_payload
            raw_categories: List[Dict[str, object]] = []
            dirty = True  # Fuerza migracion a nuevo esquema
        elif isinstance(raw_payload, dict):  # Formato nuevo con fechas y categorias
            raw_dates = list(raw_payload.get("dates", []))  # Lista de fechas
            raw_categories = list(raw_payload.get("categories", []))  # Lista de categorias
        else:
            raise ValueError("Formato invalido de almacenamiento.")

        dates: List[ImportantDate] = []  # Contenedor de fechas parseadas
        has_missing_created = any("created_at" not in item for item in raw_dates)  # Detecta legacy
        for item in raw_dates:  # Convierte cada item a modelo
            try:
                dates.append(ImportantDate.from_dict(item))  # Validacion del modelo
            except (KeyError, ValueError) as exc:
                raise ValueError(f"Item invalido encontrado en el almacenamiento: {item}") from exc

        categories, added_missing = self._load_categories(raw_categories, dates)  # Reconstruye categorias
        if not raw_categories or added_missing:
            dirty = True  # Si faltan categorias, reescribe
        if has_missing_created:
            dirty = True  # Si faltan timestamps, reescribe

        if dirty:
            self.save(StoredData(dates=dates, categories=categories))  # Persistencia con esquema nuevo

        return StoredData(dates=dates, categories=categories)

    def save(self, data: StoredData) -> None:  # Guarda el archivo
        """Guarda fechas y categorias en formato JSON legible."""
        self.path.parent.mkdir(parents=True, exist_ok=True)  # Asegura carpeta de datos

        payload = {  # Esquema nuevo con dos listas
            "dates": [item.to_dict() for item in data.dates],  # Fechas serializadas
            "categories": [category.to_dict() for category in data.categories],  # Categorias serializadas
        }
        with self.path.open("w", encoding="utf-8") as handle:  # Abre para escritura
            json.dump(payload, handle, indent=2, ensure_ascii=True)  # JSON legible

    def _load_categories(
        self, raw_categories: List[Dict[str, object]], dates: List[ImportantDate]
    ) -> tuple[List[Category], bool]:
        categories: Dict[str, Category] = {}  # Mapa por nombre en minusculas
        added_missing = False  # Marca si hubo que crear categorias nuevas
        for entry in raw_categories:  # Valida cada categoria
            try:
                category = Category.from_dict(entry)  # Parseo del modelo
            except (KeyError, ValueError) as exc:
                raise ValueError(f"Categoria invalida en almacenamiento: {entry}") from exc
            categories[category.name.lower()] = category  # Normaliza clave

        for item in dates:  # Asegura categorias usadas por fechas
            group_name = item.group or "General"  # Fallback si falta grupo
            if group_name.lower() not in categories:
                categories[group_name.lower()] = Category(name=group_name)
                added_missing = True  # Agregado por referencia en fechas

        if "general" not in categories:
            categories["general"] = Category(name="General")
            added_missing = True  # Garantiza categoria base

        return list(categories.values()), added_missing  # Devuelve lista y bandera
