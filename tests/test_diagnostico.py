"""
Pruebas del módulo de diagnóstico.

Cubren las seis preguntas del árbol de decisión (distributiva, un solo lado,
aritmética, división, signo e indeterminado). Hay tres tipos de prueba:

  1. Unitarias: un ejemplo por cada variante de error que la regla debe reconocer.
  2. Negativas: ejemplos que no deben clasificarse en esa categoría.
  3. De regresión sobre los casos del conjunto DEV del benchmark (el conjunto
     TEST no se usa aquí: está reservado para la evaluación final).
"""
import json
import pytest

from evaluacion.evaluar_diagnostico import main as evaluar_main
from evaluacion.evaluar_diagnostico import predecir
from benchmark.validar_casos import RAIZ, cargar_casos
from src.diagnostico.diagnostico import diagnosticar, obtener_categoria
from src.verificador.verificador import verificar_paso

DISTRIB = "distributiva_incorrecta"
UNLADO = "operacion_un_lado"
ARITM = "simplificacion_aritmetica"
DIV = "division_coeficiente_equivocado"
SIGNO = "error_signo"
INDET = "indeterminado"


def diagnostico_de(s_i, s_i_mas_1):
    resultado = verificar_paso(s_i, s_i_mas_1)
    assert not resultado.valido, f"'{s_i}' -> '{s_i_mas_1}' debería ser un paso inválido"
    return diagnosticar(resultado.discrepancia)


# ------------------------------------------------- 
# Distributiva: variantes
# ------------------------------------------------- 
# (paso anterior, paso del estudiante, variante esperada o None si solo importa la categoría)
DISTRIBUTIVA_EJEMPLOS = [
    ("3(x - 4) = 12", "3x - 4 = 12", None), # no multiplica el segundo término
    ("5(x + 2) = 15", "x + 10 = 15", None), # no multiplica el primer término
    ("-2(x - 3) = 8", "-2x - 6 = 8", "signo"), # factor negativo: signo equivocado adentro
    ("7 - (x - 2) = 4", "7 - x - 2 = 4", None), # signo menos delante del paréntesis
    ("2(x + 4) = 14", "2x + 6 = 14", "suma_factor"), # suma el factor en vez de multiplicar
    ("2x + 3(x - 4) = 12 - x", "2x + 3x - 7 = 12 - x", "suma_magnitudes"),
    ("(1/2)(x + 6) = 5", "x/2 + 6 = 5", None), # factor fraccionario
    ("2(x + 1) + 3(x - 2) = 9", "2x + 2 + 3x - 2 = 9", None), # varios paréntesis, el error en uno
    ("10x - 4(x + 3) + x = 18", "10x - 4x + 3 + x = 18", None), # el signo "-" queda fuera del producto
]


@pytest.mark.parametrize("s_i,s_i_mas_1,variante", DISTRIBUTIVA_EJEMPLOS)
def test_reconoce_las_variantes_de_error_en_la_distributiva(s_i, s_i_mas_1, variante):
    resultado = diagnostico_de(s_i, s_i_mas_1)
    assert resultado.categoria_id == DISTRIB
    if variante:
        assert resultado.detalles["variante"] == variante


def test_la_distributiva_informa_el_factor_involucrado():
    resultado = diagnostico_de("-2(x - 3) = 8", "-2x - 6 = 8")
    assert resultado.detalles["factor"] == "-2"


#distributiva: negativas
def test_un_denominador_que_se_quita_en_un_solo_lado_no_es_distributiva():
    # (x + 1)/2 contiene "factor * paréntesis", pero el error es multiplicar un solo lado
    resultado = diagnostico_de("(x + 1)/2 = 3", "x + 1 = 3")
    assert resultado.categoria_id == UNLADO


def test_un_error_de_signo_sin_parentesis_no_es_distributiva():
    assert diagnostico_de("2x + 3 = 11", "2x = 11 + 3").categoria_id != DISTRIB


def test_dos_errores_combinados_en_un_paso_no_son_distributiva():
    # distributiva incompleta (2*3 -> 3) + signo al pasar el -4: son dos errores
    assert diagnostico_de("2(x + 3) - 4 = 6", "2x + 3 = 6 - 4").categoria_id != DISTRIB

# ------------------------------------------------- 
# Un solo lado: variantes
# -------------------------------------------------
UN_LADO_EJEMPLOS = [
    ("2x + 3 = 11", "2x = 11"), # quita una constante de un lado y no del otro
    ("x - 5 = 9", "x = 9"),
    ("4x = x + 6", "3x = x + 6"), # resta un término con x solo en un lado
    ("x/2 + 3 = 7", "x + 6 = 7"), # multiplica solo un lado para quitar el denominador
    ("3x = 12", "x = 12"), # divide solo un lado al despejar
    ("(x + 1)/2 = 3", "x + 1 = 3"), # quita el denominador con un numerador entre paréntesis
    ("(2x + 6)/4 = 5", "2x + 6 = 5"), 
]


@pytest.mark.parametrize("s_i,s_i_mas_1", UN_LADO_EJEMPLOS)
def test_reconoce_las_variantes_de_operacion_en_un_solo_lado(s_i, s_i_mas_1):
    assert diagnostico_de(s_i, s_i_mas_1).categoria_id == UNLADO


#un solo lado: negativas
def test_pasar_un_termino_con_el_signo_equivocado_no_es_un_solo_lado():
    # el término aparece en el otro lado (con el signo mal): los dos lados cambian
    assert diagnostico_de("2x + 3 = 11", "2x = 11 + 3").categoria_id != UNLADO


def test_dividir_ambos_lados_entre_un_numero_equivocado_no_es_un_solo_lado():
    # 2x = 7 -> x = 7/4 coincide numéricamente con "multiplicar por 2 la izquierda",
    # pero el lado derecho cambió: es un error de división, no de un solo lado
    assert diagnostico_de("2x = 7", "x = 7/4").categoria_id != UNLADO


def test_un_error_al_combinar_fracciones_no_es_un_solo_lado():
    # (x - 3x)/2 coincide con "multiplicar por 2" solo por casualidad numérica,
    # pero el denominador 2 sigue escrito: no se multiplicó nada
    assert diagnostico_de("x/2 - x = -1 - 12", "(x - 3x)/2 = -13").categoria_id != UNLADO


def test_dos_errores_de_signo_en_el_mismo_paso_no_son_un_solo_lado():
    assert diagnostico_de("2x - 1 = 6 + x", "2x + x = 6 - 1").categoria_id != UNLADO


# ------------------------------------------------- 
# Aritmética: variantes
# -------------------------------------------------
# (paso anterior que muestra la operación, paso del estudiante con un número mal calculado)
ARITMETICA_EJEMPLOS = [
    ("2x = 10 - 3", "2x = 6"), # resta mal
    ("2x = -3 + 5", "2x = -8"), # suma con negativos
    ("6x - 4x + 3x = 20", "4x = 20"), # combina mal los términos con x
    ("x/2 + x/3 = 10", "2x/5 = 10"), # suma mal las fracciones
    ("x/2 + x/3 = 5", "3x + 2x = 20"), # multiplica mal por el denominador común (6*5)
    ("x = 18/6", "x = 4"), # divide mal al despejar (el divisor es el correcto)
    ("x = 12/8", "x = 2/3"), # simplifica mal la fracción
]


@pytest.mark.parametrize("s_i,s_i_mas_1", ARITMETICA_EJEMPLOS)
def test_reconoce_los_errores_de_calculo(s_i, s_i_mas_1):
    assert diagnostico_de(s_i, s_i_mas_1).categoria_id == ARITM


def test_el_calculo_informa_el_numero_que_estaba_mal():
    detalles = diagnostico_de("2x = 10 - 3", "2x = 6").detalles
    assert (detalles["valor_correcto"], detalles["valor_escrito"]) == ("7", "6")


def test_pasar_un_termino_de_lado_no_es_error_de_calculo():
    # el término cruza el "=": no es solo simplificar
    assert diagnostico_de("2x + 3 = 11", "2x = 11 + 3").categoria_id != ARITM


def test_multiplicar_un_lado_y_dividir_el_otro_no_es_error_de_calculo():
    # 8x/2 = 7 -> 8x = 7/2 coincide con "multiplicar mal por 2", pero 7/2 es 7 DIVIDIDO entre 2
    assert diagnostico_de("8x/2 = 7", "8x = 7/2").categoria_id == INDET


def test_dos_errores_de_calculo_en_el_mismo_paso_no_son_un_solo_error_de_calculo():
    assert diagnostico_de("4x + 3x - 2x = 15 - 4 + 2", "9x = 11").categoria_id == INDET


# ------------------------------------------------- 
# División: variantes
# -------------------------------------------------
DIVISION_EJEMPLOS = [
    ("4x = 20", "x = 20/3"), # divide entre otro número de la ecuación
    ("5x = 20", "x = 20/4"), # divide entre un número equivocado
    ("-3x = 12", "x = 12/3"), # coeficiente negativo: usa el valor positivo
    ("-2x = 15", "x = 15/2"),
]


@pytest.mark.parametrize("s_i,s_i_mas_1", DIVISION_EJEMPLOS)
def test_reconoce_la_division_entre_un_numero_equivocado(s_i, s_i_mas_1):
    assert diagnostico_de(s_i, s_i_mas_1).categoria_id == DIV


def test_la_division_informa_el_coeficiente_y_el_divisor_usado():
    detalles = diagnostico_de("5x = 20", "x = 20/4").detalles
    assert (detalles["coeficiente"], detalles["divisor_usado"]) == ("5", "4")


def test_dividir_bien_pero_calcular_mal_no_es_division_equivocada():
    assert diagnostico_de("x = 18/6", "x = 4").categoria_id == ARITM


def test_dividir_solo_un_lado_no_es_division_equivocada():
    assert diagnostico_de("3x = 12", "x = 12").categoria_id == UNLADO


def test_restar_o_multiplicar_en_vez_de_dividir_no_es_division_equivocada():
    assert diagnostico_de("3x = 12", "x = 12 - 3").categoria_id == INDET
    assert diagnostico_de("4x = 20", "x = 80").categoria_id == INDET


def test_con_coeficiente_fraccionario_se_multiplica_un_lado_y_se_divide_el_otro():
    # igual que en el benchmark: no es "dividir entre el número equivocado"
    assert diagnostico_de("x/2 = 11", "x = 11/2").categoria_id == INDET
    assert diagnostico_de("(2/3)x = 6", "x = 6/2").categoria_id == INDET


# ------------------------------------------------- 
# Signo: variantes
# -------------------------------------------------
SIGNO_EJEMPLOS = [
    ("6x - 4 = 3", "6x = 3 - 4"), # constante
    ("x + 5 = 9", "x = 9 + 5"),
    ("3x = x + 6", "3x + x = 6"), # término con x
    ("5x - 2 = 3x + 8", "5x - 3x = 8 - 2"), # error en el segundo término movido
]


@pytest.mark.parametrize("s_i,s_i_mas_1", SIGNO_EJEMPLOS)
def test_reconoce_el_error_de_signo_al_pasar_un_termino(s_i, s_i_mas_1):
    assert diagnostico_de(s_i, s_i_mas_1).categoria_id == SIGNO


def test_el_signo_informa_el_termino_que_cambio_de_lado():
    assert diagnostico_de("6x - 4 = 3", "6x = 3 - 4").detalles["termino"] == "-4"


# ------------------------------------------------- 
# Indeterminados: variantes
# -------------------------------------------------
INDETERMINADOS = [
    ("2x - 1 = 6 + x", "2x + x = 6 - 1"), # dos errores de signo
    ("2(x + 3) - 4 = 6", "2x + 3 = 6 - 4"), # distributiva + signo
    ("5x - 3x + 4 = 10", "3x = 10 + 4"), # cálculo + signo
    ("3x + 2 = x + 10", "3x + x = 10"), # un solo lado + signo
    ("x/2 = 11", "x = 11/2"), # multiplica un lado y divide el otro
    ("3x + 2 = 11", "5x = 11"), # suma términos que no son semejantes
]


@pytest.mark.parametrize("s_i,s_i_mas_1", INDETERMINADOS)
def test_los_errores_combinados_o_que_no_encajan_son_indeterminados(s_i, s_i_mas_1):
    assert diagnostico_de(s_i, s_i_mas_1).categoria_id == INDET


# ------------------------------------------------- 
# Detalles
# -------------------------------------------------
def test_los_detalles_solo_contienen_texto_para_poder_devolverlos_por_la_api():
    for s_i, s_i_mas_1, _ in DISTRIBUTIVA_EJEMPLOS:
        detalles = diagnostico_de(s_i, s_i_mas_1).detalles
        assert all(isinstance(v, str) for v in detalles.values())
        json.dumps(detalles)  # no debe lanzar error
    for s_i, s_i_mas_1 in UN_LADO_EJEMPLOS + ARITMETICA_EJEMPLOS + DIVISION_EJEMPLOS + SIGNO_EJEMPLOS + INDETERMINADOS:
        detalles = diagnostico_de(s_i, s_i_mas_1).detalles
        assert all(isinstance(v, str) for v in detalles.values())
        json.dumps(detalles)


def test_la_categoria_devuelta_existe_en_la_taxonomia():
    for s_i, s_i_mas_1, _ in DISTRIBUTIVA_EJEMPLOS:
        categoria = obtener_categoria(diagnostico_de(s_i, s_i_mas_1).categoria_id)
        assert categoria["id"] == DISTRIB

# ------------------------------------------------- 
# Regresión sobre los casos DEV
# -------------------------------------------------
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
    # Hoy no hay limitaciones conocidas. Si en el futuro se agrega un caso que el 
    # diagnóstico no reconoce, se debe documentar aquí.
    discrepancias = {c["id"] for c in CASOS_DEV if predicciones[c["id"]] != c["categoria"]}
    assert discrepancias == set()


#el conjunto TEST está protegido
def test_el_conjunto_test_exige_una_bandera_explicita(capsys):
    assert evaluar_main(["--conjunto", "test"]) == 1
    assert "reservado para la evaluación final" in capsys.readouterr().out
