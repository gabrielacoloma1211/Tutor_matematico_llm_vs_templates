"""
Pruebas del objeto Discrepancia del verificador.

Comprueban que, además de las formas normalizadas (ya expandidas o resueltas), la
discrepancia conserva la estructura original de cada lado de las ecuaciones,
antes de normalizar. Esa información es la que necesita el módulo de
diagnóstico para distinguir errores que, una vez expandidos, se ven idénticos.
"""
import sympy as sp
from src.verificador.verificador import verificar_paso

x = sp.symbols("x")


def test_un_paso_valido_no_genera_discrepancia():
    r = verificar_paso("3(x - 4) = 12", "3x - 12 = 12")
    assert r.valido is True
    assert r.discrepancia is None


def test_conserva_el_parentesis_del_paso_anterior_sin_expandir():
    d = verificar_paso("3(x - 4) = 12", "3x - 4 = 12").discrepancia
    assert d.izq_i.is_Mul
    assert d.der_i == 12


def test_la_expresion_original_no_esta_expandida():
    d = verificar_paso("3(x - 4) = 12", "3x - 4 = 12").discrepancia
    expandida = sp.expand(d.izq_i).doit()
    assert expandida == 3 * x - 12  # al expandirla si se obtiene la forma esperada
    assert d.izq_i != expandida  # pero lo guardado no es la forma ya expandida


def test_conserva_ambos_lados_del_paso_nuevo():
    d = verificar_paso("3(x - 4) = 12", "3x - 4 = 12").discrepancia
    assert d.izq_i_mas_1.is_Add
    assert d.der_i_mas_1 == 12


def test_las_formas_normalizadas_si_estan_expandidas_y_simplificadas():
    d = verificar_paso("3(x - 4) = 12", "3x - 4 = 12").discrepancia
    assert d.forma_normalizada_s_i == "3*x - 24"
    assert d.forma_normalizada_s_i_mas_1 == "3*x - 16"
    assert d.diferencia == "-8"


def test_dos_errores_distintos_se_ven_igual_al_normalizar_pero_no_por_estructura():
    # sin saber la forma original estos dos casos podrian ser el mismo error
    a = verificar_paso("3(x - 4) = 12", "3x - 4 = 12").discrepancia  # no multiplicó el -4 por 3
    b = verificar_paso("3x - 12 = 12", "3x - 4 = 12").discrepancia  # se cambió el término -12

    # Despues de normalizar, ambos son indistinguibles
    assert a.forma_normalizada_s_i == b.forma_normalizada_s_i
    assert a.forma_normalizada_s_i_mas_1 == b.forma_normalizada_s_i_mas_1
    assert a.diferencia == b.diferencia

    # Pero la estructura original si los distingue
    assert a.izq_i.is_Mul
    assert not b.izq_i.is_Mul
