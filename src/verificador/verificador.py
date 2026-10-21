"""
Verificador matemático determinista

Responsabilidad única: dado un paso previo (S_i) y el paso producido por el
estudiante (S_{i+1}), determina si la transformación conserva la igualdad 
y si no la conserva reporta la discrepancia simbólica exacta.

Este componente no decide qué tipo de error es (eso lo hace el módulo de
diagnóstico) ni redacta ninguna retroalimentación (eso lo hace el generador).
Su única responsabilidad es la verificación matemática.

Criterio de validez:
Un paso es válido si, al llevar S_i y S_{i+1} a la forma "expresión = 0" y
expandir completamente, las expresiones resultantes son proporcionales entre
si mediante una constante distinta de cero. Esto es equivalente a que ambas
ecuaciones tengan exactamente la misma solución.
"""
from dataclasses import dataclass, field
from typing import Optional

import sympy as sp

from src.verificador.entrada import EntradaNoPermitida, validar_ecuacion

from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

#implicit multiplication es para poder evitar el uso obligatorio de 3*x en vez de solo 3x
_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)

# Defensa adicional: parse_expr solo conoce estos nombres (no el espacio de nombres completo de
# SymPy ni el de Python). La validación previa de entrada.py ya impide cualquier otro identificador.
_NOMBRES_PERMITIDOS = {
    "Integer": sp.Integer, "Float": sp.Float, "Rational": sp.Rational, "Symbol": sp.Symbol,
    "Add": sp.Add, "Mul": sp.Mul, "Pow": sp.Pow,
}


@dataclass
class Discrepancia:
    #info simbólica sobre por qué un paso no es válido
    forma_normalizada_s_i: str
    forma_normalizada_s_i_mas_1: str
    diferencia: str
    izq_i: sp.Expr           
    der_i: sp.Expr           
    izq_i_mas_1: sp.Expr     
    der_i_mas_1: sp.Expr

    # las ecuaciones tal como se escribieron. SymPy pierde algo de estructura al
    # parsear: "3x + (x - 7)" se convierte en "3x + x - 7" y el paréntesis desaparece
    texto_i: str = ""
    texto_i_mas_1: str = ""


@dataclass
class ResultadoVerificacion:
    valido: bool
    discrepancia: Optional[Discrepancia] = None


class ErrorDeParseo(Exception):
    """
    Se lanza cuando una ecuación no puede procesarse: hay un error de entrada, no un
    error matemático. `tipo` es "error_de_formato" (mal escrita) o "entrada_no_permitida"
    (usa algo que el proyecto no admite; ver entrada.py).
    """

    def __init__(self, mensaje, tipo="error_de_formato"):
        super().__init__(mensaje)
        self.tipo = tipo


def parsear_ecuacion(ecuacion: str, variable: str = "x"):
    """
    Convierte una cadena de texto tipo "3*x + 2 = 5" en un par (lado_izq, lado_der)
    de expresiones simbólicas de SymPy.
    """
    # Antes de llamar a SymPy (parse_expr evalúa texto), la entrada pasa por la validación
    # de seguridad: caracteres, estructura, longitud y complejidad.
    try:
        validar_ecuacion(ecuacion)
    except EntradaNoPermitida as e:
        raise ErrorDeParseo(f"La ecuación '{ecuacion[:60]}' no se puede procesar: {e}.", tipo=e.tipo) from e

    partes = ecuacion.split("=")
    izq_str, der_str = partes
    simbolo = sp.symbols(variable)
    local_dict = {variable: simbolo}

    try:
        izq = parse_expr(izq_str.strip(), local_dict=local_dict, global_dict=dict(_NOMBRES_PERMITIDOS), transformations=_TRANSFORMATIONS, evaluate=False)
        der = parse_expr(der_str.strip(), local_dict=local_dict, global_dict=dict(_NOMBRES_PERMITIDOS), transformations=_TRANSFORMATIONS, evaluate=False)
    except Exception as e:
        raise ErrorDeParseo(f"No se pudo interpretar la ecuación '{ecuacion}': {e}") from e

    if any(lado.doit().has(sp.zoo, sp.nan, sp.oo, -sp.oo) for lado in (izq, der)):
        raise ErrorDeParseo(f"La ecuación '{ecuacion}' tiene una división entre cero.", tipo="entrada_no_permitida")

    return izq, der


def normalizar(izq: sp.Expr, der: sp.Expr):
    #llevamos la ecuación a la forma 'expresión = 0' y la expandimos
    return sp.expand(izq - der).doit()


def _son_proporcionales(expr1: sp.Expr, expr2: sp.Expr):
    """
    Determina si expr1 y expr2 (ya normalizadas) son
    proporcionales entre si mediante una constante k distinta de 0.
    Devuelve (son_proporcionales, k).
    """

    #casos base
    if expr1 == 0 and expr2 == 0:
        return True, sp.Integer(1)
    if expr1 == 0 or expr2 == 0:
        return False, None

    variables = expr1.free_symbols | expr2.free_symbols
    if not variables:
        # Ambas son constantes solamente numéricas 
        return (expr1 == expr2), sp.Integer(1)

    poly1 = sp.Poly(expr1, *variables)
    poly2 = sp.Poly(expr2, *variables)

    # vemos si tienen la misma estructura, osea x^2 + x^1 nunca es igual que x^2 + x^0
    if poly1.monoms() != poly2.monoms():
        return False, None

    coeficientes1 = poly1.coeffs()
    coeficientes2 = poly2.coeffs()

    if any(c2 == 0 for c2 in coeficientes2):
        return False, None

    razones = [sp.nsimplify(c1 / c2) for c1, c2 in zip(coeficientes1, coeficientes2)]
    primera_razon = razones[0]

    if primera_razon == 0:
        return False, None

    if all(r == primera_razon for r in razones):
        return True, primera_razon

    return False, None


def ecuaciones_equivalentes(izq_a: sp.Expr, der_a: sp.Expr, izq_b: sp.Expr, der_b: sp.Expr) -> bool:
    """
    Indica si las ecuaciones A y B son equivalentes (tienen la misma solución).

    Es el mismo criterio de validez que usa verificar_paso: llevar cada
    ecuación a la forma "expresión = 0", expandir, y comprobar que las dos
    expresiones son proporcionales. Está disponible para que otros módulos
    (por ejemplo, el de diagnóstico) comparen ecuaciones sin repetir esta lógica.
    """
    proporcionales, _k = _son_proporcionales(normalizar(izq_a, der_a), normalizar(izq_b, der_b))
    return proporcionales


def verificar_paso(s_i: str, s_i_mas_1: str, variable: str = "x") -> ResultadoVerificacion:
    """
    Verifica si el paso de S_i a S_{i+1} conserva la solución de la ecuación.

    """
    izq_i, der_i = parsear_ecuacion(s_i, variable)
    izq_i1, der_i1 = parsear_ecuacion(s_i_mas_1, variable)

    norm_i = normalizar(izq_i, der_i)
    norm_i1 = normalizar(izq_i1, der_i1)

    proporcionales, _k = _son_proporcionales(norm_i, norm_i1)

    if proporcionales:
        return ResultadoVerificacion(valido=True)

    diferencia = sp.expand(norm_i - norm_i1).doit()
    return ResultadoVerificacion(
        valido=False,
        discrepancia=Discrepancia(
            forma_normalizada_s_i=str(norm_i),
            forma_normalizada_s_i_mas_1=str(norm_i1),
            diferencia=str(diferencia),
            izq_i=izq_i,              
            der_i=der_i,              
            izq_i_mas_1=izq_i1,       
            der_i_mas_1=der_i1,
            texto_i=s_i,
            texto_i_mas_1=s_i_mas_1,
        ),
    )

