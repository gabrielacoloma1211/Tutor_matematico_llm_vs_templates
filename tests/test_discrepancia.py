"""
Pruebas del objeto Discrepancia del verificador.

Comprueban que, además de las formas normalizadas (ya expandidas o resueltas), la
discrepancia conserva la estructura original de cada lado de las ecuaciones,
antes de normalizar. Esa información es la que necesita el módulo de
diagnóstico para distinguir errores que, una vez expandidos, se ven idénticos.

Las ecuaciones y los valores esperados están en tests/datos/discrepancia.json.
"""
import sympy as sp

from src.verificador.verificador import verificar_paso
from tests.datos import cargar

DATOS = cargar("discrepancia")


def _paso(nombre):
    return DATOS[nombre]["s_i"], DATOS[nombre]["s_i_mas_1"]


def _discrepancia(nombre):
    return verificar_paso(*_paso(nombre)).discrepancia


def _tipo(expresion):
    return type(expresion).__name__  # "Mul" si es un producto, "Add" si es una suma


def test_un_paso_valido_no_genera_discrepancia():
    r = verificar_paso(*_paso("paso_valido"))
    assert r.valido is True
    assert r.discrepancia is None


def test_conserva_el_parentesis_del_paso_anterior_sin_expandir():
    esperado = DATOS["distributiva_incompleta"]["esperado"]
    d = _discrepancia("distributiva_incompleta")
    assert _tipo(d.izq_i) == esperado["tipo_izq_i"]
    assert d.der_i == sp.sympify(esperado["der_i"])


def test_la_expresion_original_no_esta_expandida():
    esperado = DATOS["distributiva_incompleta"]["esperado"]
    d = _discrepancia("distributiva_incompleta")
    expandida = sp.expand(d.izq_i).doit()
    assert expandida == sp.sympify(esperado["izq_i_expandida"])  # al expandirla sí se obtiene la forma esperada
    assert d.izq_i != expandida  # pero lo guardado no es la forma ya expandida


def test_conserva_ambos_lados_del_paso_nuevo():
    esperado = DATOS["distributiva_incompleta"]["esperado"]
    d = _discrepancia("distributiva_incompleta")
    assert _tipo(d.izq_i_mas_1) == esperado["tipo_izq_i_mas_1"]
    assert d.der_i_mas_1 == sp.sympify(esperado["der_i_mas_1"])


def test_las_formas_normalizadas_si_estan_expandidas_y_simplificadas():
    esperado = DATOS["distributiva_incompleta"]["esperado"]
    d = _discrepancia("distributiva_incompleta")
    assert d.forma_normalizada_s_i == esperado["forma_normalizada_s_i"]
    assert d.forma_normalizada_s_i_mas_1 == esperado["forma_normalizada_s_i_mas_1"]
    assert d.diferencia == esperado["diferencia"]


def test_dos_errores_distintos_se_ven_igual_al_normalizar_pero_no_por_estructura():
    # sin saber la forma original estos dos casos podrían ser el mismo error
    a = _discrepancia("distributiva_incompleta")
    b = _discrepancia("otro_origen_mismo_resultado")

    # Después de normalizar, ambos son indistinguibles
    assert a.forma_normalizada_s_i == b.forma_normalizada_s_i
    assert a.forma_normalizada_s_i_mas_1 == b.forma_normalizada_s_i_mas_1
    assert a.diferencia == b.diferencia

    # Pero la estructura original sí los distingue
    assert _tipo(a.izq_i) == DATOS["distributiva_incompleta"]["esperado"]["tipo_izq_i"]
    assert _tipo(b.izq_i) == DATOS["otro_origen_mismo_resultado"]["esperado"]["tipo_izq_i"]
    assert _tipo(a.izq_i) != _tipo(b.izq_i)
