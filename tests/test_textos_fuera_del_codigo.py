"""Los textos que ve el estudiante (pistas, prompt del LLM, avisos) viven en archivos de data/, no en el código.

Misma idea que test_ejemplos_fuera_del_codigo: el código solo los carga. Así se pueden revisar y cambiar
sin tocar el programa, y quedan en un solo lugar para la tesis.
"""
import ast
import json
import re
from pathlib import Path

import pytest

from src.generador import llm
from src.generador.plantillas import RUTA_TEXTOS, TEXTOS

RAIZ = Path(__file__).resolve().parent.parent
PREFIJOS = ("PLANTILLA_", "PISTAS_", "MENSAJE_", "PROMPT_")
MODULOS = [RAIZ / "src" / "generador" / "plantillas.py", RAIZ / "src" / "generador" / "llm.py"]
MARCADORES_PERMITIDOS = {"{termino}", "{factor}", "{coeficiente}", "{multiplicador}", "{lado}", "{operacion}"}


def _hojas_de_texto(valor):
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for v in valor.values():
            yield from _hojas_de_texto(v)


@pytest.mark.parametrize("modulo", MODULOS, ids=lambda p: p.name)
def test_las_constantes_de_texto_se_cargan_de_data_y_no_son_literales(modulo):
    arbol = ast.parse(modulo.read_text(encoding="utf-8"))
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign):
            for destino in nodo.targets:
                if isinstance(destino, ast.Name) and destino.id.startswith(PREFIJOS):
                    assert not isinstance(nodo.value, (ast.Constant, ast.Dict, ast.JoinedStr, ast.BinOp)), (
                        f"{modulo.name}: {destino.id} tiene el texto escrito en el código; va en data/")


def test_el_archivo_de_plantillas_tiene_textos_completos_y_marcadores_validos():
    assert RUTA_TEXTOS.is_file()
    datos = json.loads(RUTA_TEXTOS.read_text(encoding="utf-8"))
    assert datos == TEXTOS
    textos = list(_hojas_de_texto(datos))
    assert textos and all(t.strip() for t in textos)
    for t in textos:
        assert set(re.findall(r"\{\w+\}", t)) <= MARCADORES_PERMITIDOS


def test_el_prompt_del_llm_esta_en_un_archivo_y_tiene_sus_marcadores():
    assert llm.RUTA_PROMPT.is_file()
    texto = llm.RUTA_PROMPT.read_text(encoding="utf-8")
    assert texto == llm.PROMPT_SISTEMA
    assert "{nombre_categoria}" in texto and "{definicion_categoria}" in texto
