"""
Datos de prueba.

Los ejemplos de pasos de estudiantes (ecuaciones y la categoría o el resultado
esperado) NO se escriben en el código de las pruebas: viven en los archivos
JSON de esta carpeta y las pruebas solo los cargan con `cargar`.
"""
import json
from pathlib import Path

_CARPETA = Path(__file__).resolve().parent


def cargar(nombre):
    """Lee tests/datos/<nombre>.json y devuelve su contenido."""
    with open(_CARPETA / f"{nombre}.json", encoding="utf-8") as f:
        return json.load(f)
