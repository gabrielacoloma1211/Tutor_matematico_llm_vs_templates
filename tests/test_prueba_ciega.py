"""
Pruebas de la prueba ciega (100 casos generados por un LLM, solo para medir).

Los casos se agregan después; mientras el archivo no exista, las pruebas sobre
los casos se omiten. Las pruebas del script no dependen de los casos.
"""
import json

import pytest

from benchmark.validar_casos import CATEGORIAS, validar_caso
from evaluacion import evaluar_prueba_ciega as pc

HAY_CASOS = pc.ARCHIVO.exists()
CASOS = json.loads(pc.ARCHIVO.read_text(encoding="utf-8")) if HAY_CASOS else []


def test_la_huella_del_codigo_es_estable_y_tiene_16_caracteres():
    assert pc.huella_codigo() == pc.huella_codigo()
    assert len(pc.huella_codigo()) == 16


def test_el_script_exige_confirmar_que_no_se_ajusta():
    assert pc.main([]) == 2


@pytest.mark.skipif(not HAY_CASOS, reason="todavía no se cargaron los casos de la prueba ciega")
def test_la_prueba_ciega_tiene_100_casos_con_ids_unicos():
    assert len(CASOS) == 100
    assert len({c["id"] for c in CASOS}) == 100


@pytest.mark.skipif(not HAY_CASOS, reason="todavía no se cargaron los casos de la prueba ciega")
@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_cada_caso_de_la_prueba_ciega_es_consistente(caso):
    assert validar_caso(caso) == []
    assert caso["categoria"] in CATEGORIAS
    assert caso["tipo_de_novedad"] in pc.TIPOS


@pytest.mark.skipif(not HAY_CASOS, reason="todavía no se cargaron los casos de la prueba ciega")
def test_los_casos_no_repiten_ecuaciones_de_los_otros_conjuntos():
    from benchmark.validar_casos import RAIZ

    otros = set()
    for ruta in (RAIZ / "benchmark" / "casos").rglob("*.json"):
        if ruta.parent.name == "prueba_ciega":
            continue
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        if isinstance(datos, list):
            otros |= {c["solucion_correcta"][0].replace(" ", "") for c in datos if isinstance(c, dict) and "solucion_correcta" in c}
    repetidas = [c["id"] for c in CASOS if c["solucion_correcta"][0].replace(" ", "") in otros]
    assert repetidas == []
