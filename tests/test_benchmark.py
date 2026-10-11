"""
Pruebas del benchmark

1) Cada caso del conjunto dev debe ser matemáticamente consistente
   (se valida con el verificador determinista).
2) El propio validador debe detectar casos mal construidos; si no lo hiciera,
   un caso con errores podría ser incluido en el benchmark.
"""
import copy
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


@pytest.fixture
def caso_valido():
    # primer ejemplo (error de signo), copiado para poder modificarlo
    return copy.deepcopy(CASOS_EJEMPLO[0][1])


def test_detecta_paso_marcado_como_erroneo_que_en_realidad_es_valido(caso_valido):
    i = caso_valido["indice_paso_erroneo"]
    caso_valido["resolucion_estudiante"][i] = caso_valido["correccion_esperada"]
    errores = validar_caso(caso_valido)
    assert any("VÁLIDO" in e for e in errores)


def test_detecta_error_en_un_paso_que_no_es_el_marcado(caso_valido):
    caso_valido["indice_paso_erroneo"] += 1  # el error real queda un paso antes
    assert validar_caso(caso_valido) != []


def test_detecta_correccion_esperada_invalida(caso_valido):
    i = caso_valido["indice_paso_erroneo"]
    caso_valido["correccion_esperada"] = caso_valido["resolucion_estudiante"][i]  # el paso con error
    errores = validar_caso(caso_valido)
    assert any("correccion_esperada" in e for e in errores)


def test_detecta_solucion_correcta_con_un_paso_invalido(caso_valido):
    caso_valido["solucion_correcta"][2] = "6x = 8"
    errores = validar_caso(caso_valido)
    assert any("solucion_correcta" in e for e in errores)


def test_detecta_campo_faltante(caso_valido):
    del caso_valido["pista_referencia"]
    errores = validar_caso(caso_valido)
    assert any("faltan campos" in e for e in errores)


def test_detecta_categoria_inexistente(caso_valido):
    caso_valido["categoria"] = "error_inventado"
    errores = validar_caso(caso_valido)
    assert any("no existe en la taxonomía" in e for e in errores)


def test_detecta_indice_fuera_de_rango(caso_valido):
    caso_valido["indice_paso_erroneo"] = 99
    assert validar_caso(caso_valido) != []


def test_reporta_ecuacion_que_no_se_puede_interpretar(caso_valido):
    caso_valido["solucion_correcta"][1] = "6x = = 3"
    errores = validar_caso(caso_valido)
    assert any("no se pudo interpretar" in e for e in errores)


def test_detecta_caracteres_que_sympy_interpretaria_mal(caso_valido):
    # el signo menos "−" (U+2212) que usa word, no da error de parseo
    # en SymPy sino una interpretación incorrecta; el validador debe rechazarlo
    caso_valido["solucion_correcta"][0] = "6x \u2212 4 = 3"
    caso_valido["resolucion_estudiante"][0] = "6x \u2212 4 = 3"
    errores = validar_caso(caso_valido)
    assert any("caracteres no permitidos" in e for e in errores)
