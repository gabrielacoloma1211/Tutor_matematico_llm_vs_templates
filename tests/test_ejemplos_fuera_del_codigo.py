"""
Los ejemplos de pasos de estudiantes no se escriben en el código de las pruebas:
viven en tests/datos/*.json y las pruebas solo los cargan.

Esta prueba lo vigila. Revisa el código de cada archivo de pruebas y falla si
encuentra una cadena que parece una ecuación (por ejemplo "x + 5 = 12"). Los
comentarios y las descripciones (docstrings) no cuentan.
"""
import ast
import re
from pathlib import Path

import pytest

CARPETA = Path(__file__).resolve().parent
ARCHIVOS = sorted(p for p in CARPETA.glob("test_*.py") if p.name != Path(__file__).name)


def _cadenas_del_codigo(archivo):
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    descripciones = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.ClassDef)) and nodo.body:
            primera = nodo.body[0]
            if isinstance(primera, ast.Expr) and isinstance(primera.value, ast.Constant) and isinstance(primera.value.value, str):
                descripciones.add(id(primera.value))
    return [
        n.value
        for n in ast.walk(arbol)
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in descripciones
    ]


def _parece_una_ecuacion(texto):
    return "=" in texto and re.search(r"\d|\bx\b", texto) is not None and not texto.startswith("--")


@pytest.mark.parametrize("archivo", ARCHIVOS, ids=[a.name for a in ARCHIVOS])
def test_el_codigo_de_las_pruebas_no_tiene_ecuaciones_escritas(archivo):
    encontradas = [c for c in _cadenas_del_codigo(archivo) if _parece_una_ecuacion(c)]
    assert encontradas == [], f"Ecuaciones escritas en el código de {archivo.name}: muévelas a tests/datos/*.json"
