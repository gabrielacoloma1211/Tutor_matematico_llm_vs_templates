"""
Pruebas del módulo de diagnóstico.

Cubren las seis preguntas del árbol de decisión (distributiva, un solo lado,
aritmética, división, signo e indeterminado). Hay tres tipos de prueba:

  1. Unitarias: un ejemplo por cada variante de error que la regla debe reconocer.
  2. Negativas (de frontera): ejemplos que NO deben clasificarse en una categoría
     parecida. Son tan importantes como las anteriores: un diagnóstico que
     clasifica todo como distributiva tendría "recall perfecto" y no serviría de nada.
  3. De regresión sobre los casos del conjunto DEV del benchmark (el conjunto
     TEST no se usa aquí: está reservado para la evaluación final).

Los ejemplos de los puntos 1 y 2 (el paso anterior, el paso del estudiante, la
categoría esperada y, cuando importa, los detalles esperados) están en
tests/datos/diagnostico.json, no en el código.
"""
import json

import pytest

from evaluacion.evaluar_diagnostico import main as evaluar_main
from evaluacion.evaluar_diagnostico import predecir
from benchmark.validar_casos import RAIZ, cargar_casos
from src.diagnostico.diagnostico import diagnosticar, obtener_categoria
from src.verificador.verificador import verificar_paso
from tests.datos import cargar

DISTRIB = "distributiva_incorrecta"
UNLADO = "operacion_un_lado"
ARITM = "simplificacion_aritmetica"
DIV = "division_coeficiente_equivocado"
SIGNO = "error_signo"
INDET = "indeterminado"

EJEMPLOS = cargar("diagnostico")
IDS = [f"{e['grupo']}-{e['id']}" for e in EJEMPLOS]
CON_DETALLES = [e for e in EJEMPLOS if "detalles" in e]
IDS_CON_DETALLES = [f"{e['grupo']}-{e['id']}" for e in CON_DETALLES]


def diagnostico_de(s_i, s_i_mas_1):
    resultado = verificar_paso(s_i, s_i_mas_1)
    assert not resultado.valido, f"'{s_i}' -> '{s_i_mas_1}' debería ser un paso inválido"
    return diagnosticar(resultado.discrepancia)


# ------------------------------------------- ejemplos (variantes y fronteras)
@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=IDS)
def test_el_diagnostico_asigna_la_categoria_esperada(ejemplo):
    resultado = diagnostico_de(ejemplo["s_i"], ejemplo["s_i_mas_1"])
    assert resultado.categoria_id == ejemplo["categoria_esperada"], ejemplo["descripcion"]


@pytest.mark.parametrize("ejemplo", CON_DETALLES, ids=IDS_CON_DETALLES)
def test_el_diagnostico_informa_los_detalles_esperados(ejemplo):
    detalles = diagnostico_de(ejemplo["s_i"], ejemplo["s_i_mas_1"]).detalles
    for clave, valor in ejemplo["detalles"].items():
        assert detalles[clave] == valor, f"detalle '{clave}': {ejemplo['descripcion']}"


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=IDS)
def test_los_detalles_solo_contienen_texto_para_poder_devolverlos_por_la_api(ejemplo):
    detalles = diagnostico_de(ejemplo["s_i"], ejemplo["s_i_mas_1"]).detalles
    assert all(isinstance(v, str) for v in detalles.values())
    json.dumps(detalles)  # no debe lanzar error


@pytest.mark.parametrize("ejemplo", EJEMPLOS, ids=IDS)
def test_la_categoria_devuelta_existe_en_la_taxonomia(ejemplo):
    categoria = obtener_categoria(diagnostico_de(ejemplo["s_i"], ejemplo["s_i_mas_1"]).categoria_id)
    assert categoria["id"] == ejemplo["categoria_esperada"]


# ------------------------------------------ los datos de las pruebas
def test_los_ejemplos_cubren_las_seis_categorias():
    assert {e["categoria_esperada"] for e in EJEMPLOS} == {DISTRIB, UNLADO, ARITM, DIV, SIGNO, INDET}


def test_los_ejemplos_no_repiten_ids_ni_pasos():
    pares = [(e["s_i"], e["s_i_mas_1"]) for e in EJEMPLOS]
    assert len(set(IDS)) == len(IDS)
    assert len(set(pares)) == len(pares)


# --------------------------------------- regresión sobre los casos DEV
DIR_DEV = RAIZ / "benchmark" / "casos" / "dev"
CASOS_DEV = [c for _, c in cargar_casos(DIR_DEV)] if DIR_DEV.exists() else []

@pytest.fixture(scope="module")
def predicciones():
    return {c["id"]: predecir(c) for c in CASOS_DEV}


@pytest.mark.skipif(not CASOS_DEV, reason="todavía no hay casos dev")
def test_todos_los_casos_dev_de_distributiva_se_reconocen(predicciones):
    reales = {c["id"] for c in CASOS_DEV if c["categoria"] == DISTRIB}
    detectados = {i for i in reales if predicciones[i] == DISTRIB}
    assert detectados == reales


@pytest.mark.skipif(not CASOS_DEV, reason="todavía no hay casos dev")
def test_ningun_caso_dev_de_otra_categoria_se_clasifica_como_distributiva(predicciones):
    intrusos = [c["id"] for c in CASOS_DEV if c["categoria"] != DISTRIB and predicciones[c["id"]] == DISTRIB]
    assert intrusos == []


@pytest.mark.skipif(not CASOS_DEV, reason="todavía no hay casos dev")
def test_todos_los_casos_dev_de_un_solo_lado_se_reconocen(predicciones):
    reales = {c["id"] for c in CASOS_DEV if c["categoria"] == UNLADO}
    detectados = {i for i in reales if predicciones[i] == UNLADO}
    assert detectados == reales


@pytest.mark.skipif(not CASOS_DEV, reason="todavía no hay casos dev")
def test_ningun_caso_dev_de_otra_categoria_se_clasifica_como_un_solo_lado(predicciones):
    intrusos = [c["id"] for c in CASOS_DEV if c["categoria"] != UNLADO and predicciones[c["id"]] == UNLADO]
    assert intrusos == []


@pytest.mark.skipif(not CASOS_DEV, reason="todavía no hay casos dev")
def test_el_diagnostico_coincide_con_la_categoria_de_la_autora_en_los_casos_dev(predicciones):
    # Hoy no hay limitaciones conocidas. Si en el futuro se agrega un caso que el diagnóstico
    # no reconoce, se debe documentar aquí en vez de ocultarlo.
    discrepancias = {c["id"] for c in CASOS_DEV if predicciones[c["id"]] != c["categoria"]}
    assert discrepancias == set()


# ------------------------------ el conjunto TEST está protegido
def test_el_conjunto_test_exige_una_bandera_explicita(capsys):
    assert evaluar_main(["--conjunto", "test"]) == 1
    assert "reservado para la evaluación final" in capsys.readouterr().out
