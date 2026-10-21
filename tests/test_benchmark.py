"""
Pruebas del benchmark

1) Cada caso del conjunto dev debe ser matemáticamente consistente
   (se valida con el verificador determinista).
2) El propio validador debe detectar casos mal construidos; si no lo hiciera,
   un caso con errores podría ser incluido en el benchmark.

Los casos mal construidos (copias de un ejemplo con un defecto cada una) están
en tests/datos/casos_mal_armados.json.
"""
from collections import Counter

import pytest

from benchmark.validar_casos import (
    CATEGORIAS,
    OBJETIVO_DEV,
    OBJETIVO_TEST,
    RAIZ,
    cargar_casos,
    validar_caso,
)
from tests.datos import cargar

DIR_DEV = RAIZ / "benchmark" / "casos" / "dev"
DIR_TEST = RAIZ / "benchmark" / "casos" / "test"
DIR_EJEMPLOS = RAIZ / "benchmark" / "casos" / "ejemplos"

CASOS_DEV = cargar_casos(DIR_DEV) if DIR_DEV.exists() else []
CASOS_TEST = cargar_casos(DIR_TEST) if DIR_TEST.exists() else []
CASOS_EJEMPLO = cargar_casos(DIR_EJEMPLOS)


def _ids(casos):
    return [c.get("id", "sin-id") for _, c in casos]


# casos dev
@pytest.mark.parametrize("archivo,caso", CASOS_DEV, ids=_ids(CASOS_DEV))
def test_caso_dev_es_consistente(archivo, caso):
    assert validar_caso(caso) == []


def test_ids_del_conjunto_dev_no_se_repiten():
    repetidos = [i for i, n in Counter(c.get("id") for _, c in CASOS_DEV).items() if n > 1]
    assert repetidos == []


# casos test
@pytest.mark.parametrize("archivo,caso", CASOS_TEST, ids=_ids(CASOS_TEST))
def test_caso_test_es_consistente(archivo, caso):
    assert validar_caso(caso) == []


def test_ids_de_dev_y_test_no_se_repiten():
    todos = [c.get("id") for _, c in CASOS_DEV + CASOS_TEST]
    assert [i for i, n in Counter(todos).items() if n > 1] == []


def test_los_ids_corresponden_al_conjunto_en_el_que_estan():
    assert all(c["id"].startswith("DEV-") for _, c in CASOS_DEV)
    assert all(c["id"].startswith("TEST-") for _, c in CASOS_TEST)


# composición del benchmark
@pytest.mark.skipif(not CASOS_DEV, reason="todavía no hay casos dev")
def test_distribucion_de_dev_cumple_el_objetivo():
    assert dict(Counter(c["categoria"] for _, c in CASOS_DEV)) == OBJETIVO_DEV


@pytest.mark.skipif(not CASOS_TEST, reason="todavía no hay casos test")
def test_distribucion_de_test_cumple_el_objetivo():
    assert dict(Counter(c["categoria"] for _, c in CASOS_TEST)) == OBJETIVO_TEST


@pytest.mark.skipif(not (CASOS_DEV and CASOS_TEST), reason="faltan casos dev o test")
def test_dev_y_test_no_comparten_ecuaciones_iniciales():
    #que no se repitan entre test y dev
    inicial = lambda c: c["solucion_correcta"][0].replace(" ", "")
    comunes = {inicial(c) for _, c in CASOS_DEV} & {inicial(c) for _, c in CASOS_TEST}
    assert comunes == set()


@pytest.mark.parametrize("archivo,caso", CASOS_DEV + CASOS_TEST, ids=_ids(CASOS_DEV + CASOS_TEST))
def test_cada_caso_tiene_pista_y_los_indeterminados_tienen_nota(archivo, caso):
    assert caso["pista_referencia"].strip() != ""
    if caso["categoria"] == "indeterminado":
        assert caso.get("notas", "").strip() != ""


# el validador funciona
@pytest.mark.parametrize("archivo,caso", CASOS_EJEMPLO, ids=_ids(CASOS_EJEMPLO))
def test_los_ejemplos_de_formato_son_consistentes(archivo, caso):
    assert validar_caso(caso) == []


def test_los_ejemplos_cubren_todas_las_categorias():
    assert {c["categoria"] for _, c in CASOS_EJEMPLO} == set(CATEGORIAS)


DEFECTOS = cargar("casos_mal_armados")


@pytest.mark.parametrize("defecto", DEFECTOS, ids=[d["id"] for d in DEFECTOS])
def test_el_validador_detecta_los_casos_mal_armados(defecto):
    errores = validar_caso(defecto["caso"])
    assert errores != [], defecto["descripcion"]
    if defecto["error_esperado"]:
        assert any(defecto["error_esperado"] in e for e in errores), defecto["descripcion"]


BIEN_ARMADOS = cargar("casos_bien_armados")


@pytest.mark.parametrize("ejemplo", BIEN_ARMADOS, ids=[e["id"] for e in BIEN_ARMADOS])
def test_el_validador_acepta_variantes_validas_de_enunciado_y_despeje(ejemplo):
    assert validar_caso(ejemplo["caso"]) == []


def _casos_json(ruta):
    import json
    return json.loads((RAIZ / "benchmark" / "casos" / ruta).read_text(encoding="utf-8"))


def test_el_conjunto_ampliado_cumple_enunciado_y_despeje():
    casos = _casos_json("ampliado/ampliado.json")
    assert len(casos) == 100
    assert [c["id"] for c in casos if validar_caso(c)] == []


def test_las_variaciones_se_validan_sin_exigir_despeje():
    casos = _casos_json("variaciones/variaciones.json") + _casos_json("variaciones/variaciones_nuevas.json")
    assert [c["id"] for c in casos if validar_caso(c, exigir_despeje=False)] == []
    assert all(validar_caso(c) for c in casos)  # con la exigencia completa no son casos de benchmark
