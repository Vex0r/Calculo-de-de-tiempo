"""Persistencia en JSON para las fechas."""  # Explica el modulo

from __future__ import annotations  # Permite tipos adelantados

import json  # Maneja JSON
from pathlib import Path  # Maneja rutas
from typing import List  # Tipos para listas

from .models import ImportantDate  # Modelo principal


class JsonStorage:  # Clase de guardado
    """Carga y guarda fechas importantes en JSON."""  # Resume la clase

    def __init__(self, path: Path) -> None:  # Guarda la ruta del archivo
        self.path = path  # Ruta donde se guarda el JSON

    def load(self) -> List[ImportantDate]:  # Lee el archivo
        """Lee el archivo y devuelve fechas validas."""  # Resume la funcion
        if not self.path.exists():  # Si no existe el archivo
            return []  # Devuelve lista vacia

        try:  # Intenta leer el JSON
            with self.path.open("r", encoding="utf-8") as handle:  # Abre el archivo
                raw_items = json.load(handle)  # Carga el contenido
        except json.JSONDecodeError as exc:  # Captura JSON roto
            raise json.JSONDecodeError(f"El archivo {self.path} esta corrupto.", exc.doc, exc.pos) from exc  # Aviso claro

        results: List[ImportantDate] = []  # Lista para resultados
        has_missing_created = any("created_at" not in item for item in raw_items)  # Revisa migracion
        for item in raw_items:  # Recorre items crudos
            try:  # Intenta convertir
                results.append(ImportantDate.from_dict(item))  # Convierte a modelo
            except (KeyError, ValueError) as exc:  # Si falla el formato
                raise ValueError(f"Item invalido encontrado en el almacenamiento: {item}") from exc  # Falla claro

        if has_missing_created:  # Si faltaba created_at
            self.save(results)  # Guarda de nuevo con el dato

        return results  # Devuelve la lista final

    def save(self, items: List[ImportantDate]) -> None:  # Guarda el archivo
        """Guarda la lista en formato JSON legible."""  # Resume la funcion
        self.path.parent.mkdir(parents=True, exist_ok=True)  # Crea carpeta si falta

        payload = [item.to_dict() for item in items]  # Convierte a dicts
        with self.path.open("w", encoding="utf-8") as handle:  # Abre para escribir
            json.dump(payload, handle, indent=2, ensure_ascii=True)  # Guarda el JSON
