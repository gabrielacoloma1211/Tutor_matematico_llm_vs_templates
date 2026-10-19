"""
Pruebas de `ecuaciones_equivalentes`.

El módulo de diagnóstico y `verificar_paso` deben usar la MISMA definición de
"equivalente". Por eso la prueba más importante es la de coherencia: para
cualquier par de pasos, `ecuaciones_equivalentes` tiene que coincidir con lo
que decide `verificar_paso`.

Los pares de ecuaciones están en tests/datos/equivalencia.json.
"""
import pytest

from src.verificador.verificador import ecuaciones_equivalentes, parsear_ecuacion, verificar_paso
from tests.datos import cargar

DATOS = cargar("equivalencia")
EQUIVALENTES = DATOS["equivalentes"]
NO_EQUIVALENTES = DATOS["no_equivalentes"]
TODOS = EQUIVALENTES + NO_EQUIVALENTES


def _ids(lista):
    return [p["id"] for p in lista]


def _comparar(par):
    izq_a, der_a = parsear_ecuacion(par["ecuacion_a"])
    izq_b, der_b = parsear_ecuacion(par["ecuacion_b"])
    return ecuaciones_equivalentes(izq_a, der_a, izq_b, der_b)


@pytest.mark.parametrize("par", EQUIVALENTES, ids=_ids(EQUIVALENTES))
def test_reconoce_ecuaciones_equivalentes(par):
    assert _comparar(par) is True


@pytest.mark.parametrize("par", NO_EQUIVALENTES, ids=_ids(NO_EQUIVALENTES))
def test_reconoce_ecuaciones_no_equivalentes(par):
    assert _comparar(par) is False


@pytest.mark.parametrize("par", TODOS, ids=[f"{'si' if p in EQUIVALENTES else 'no'}-{p['id']}" for p in TODOS])
def test_coincide_siempre_con_la_decision_de_verificar_paso(par):
    assert _comparar(par) == verificar_paso(par["ecuacion_a"], par["ecuacion_b"]).valido
