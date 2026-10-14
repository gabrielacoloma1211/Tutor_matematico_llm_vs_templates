"""
Pruebas de `ecuaciones_equivalentes`.

El módulo de diagnóstico y `verificar_paso` deben usar la MISMA definición de
"equivalente". Por eso la prueba más importante es la de coherencia: para
cualquier par de pasos, `ecuaciones_equivalentes` tiene que coincidir con lo
que decide `verificar_paso`.
"""
import pytest

from src.verificador.verificador import ecuaciones_equivalentes, parsear_ecuacion, verificar_paso

EQUIVALENTES = [
    ("6x - 4 = 3", "6x = 3 + 4"), # transponer un término
    ("x + 5 = 12", "2x + 10 = 24"), # multiplicar ambos lados
    ("3(x - 4) = 12", "3x - 12 = 12"), # propiedad distributiva bien aplicada
    ("x + 5 = 12", "12 = x + 5"), # intercambiar los lados
    ("x/2 + 3 = 7", "x + 6 = 14"), # quitar un denominador en ambos lados
]
NO_EQUIVALENTES = [
    ("6x - 4 = 3", "6x = 3 - 4"), # error de signo
    ("3(x - 4) = 12", "3x - 4 = 12"), # distributiva incompleta
    ("2x + 3 = 11", "2x = 11"), # operación en un solo lado
    ("5x = 20", "x = 5"), # división entre un número equivocado
]


def _comparar(par):
    izq_a, der_a = parsear_ecuacion(par[0])
    izq_b, der_b = parsear_ecuacion(par[1])
    return ecuaciones_equivalentes(izq_a, der_a, izq_b, der_b)


@pytest.mark.parametrize("par", EQUIVALENTES)
def test_reconoce_ecuaciones_equivalentes(par):
    assert _comparar(par) is True


@pytest.mark.parametrize("par", NO_EQUIVALENTES)
def test_reconoce_ecuaciones_no_equivalentes(par):
    assert _comparar(par) is False


@pytest.mark.parametrize("par", EQUIVALENTES + NO_EQUIVALENTES)
def test_coincide_siempre_con_la_decision_de_verificar_paso(par):
    assert _comparar(par) == verificar_paso(par[0], par[1]).valido


def test_funciona_con_expresiones_sin_evaluar():
    # el diagnóstico la usa con los árboles originales de S_i
    izq, der = parsear_ecuacion("3(x - 4) = 12")
    assert ecuaciones_equivalentes(izq, der, *parsear_ecuacion("x - 4 = 4"))
