"""Generador de retroalimentación con plantillas contextualizadas.

Toma el resultado del diagnóstico y rellena la plantilla de la categoría con
los datos del paso del estudiante (término, factor, coeficiente). No usa LLM:
es determinista y no inventa contenido.
"""
import re
from fractions import Fraction

import sympy as sp

from src.diagnostico.diagnostico import ResultadoDiagnostico, obtener_categoria
from src.verificador.verificador import ErrorDeParseo, parsear_ecuacion

MENSAJE_GENERAL = (
    "Revisa este paso con más cuidado. No pudimos identificar el tipo exacto de error."
)

# El diagnóstico llama error_signo a varias situaciones y la plantilla de la taxonomía ("al moverlo
# al otro lado, su signo debe cambiar") solo describe una. Según cómo escribió el estudiante el
# término, se elige entre estas pistas; ninguna dice que el término cambió de lado si no lo hizo.
PLANTILLA_SIGNO_MISMO_LADO = (
    "Revisa el signo del término {termino}: como sigue en el mismo lado de la ecuación, "
    "su signo no debe cambiar."
)
PLANTILLA_SIGNO_NEUTRA = (
    "Revisa los signos de este paso: un término solo cambia de signo cuando lo pasas "
    "al otro lado de la ecuación."
)
PLANTILLA_SIGNO_AL_MULTIPLICAR = (
    "Al multiplicar por {multiplicador}, cada término conserva su signo: "
    "revisa los signos de tu resultado."
)
PLANTILLA_SIGNO_OPERACION_OPUESTA = (
    "Revisa los signos: si sumas o restas {termino} en los dos lados de la ecuación, "
    "la operación debe ser la misma en cada lado."
)
PLANTILLA_SIGNO_PARENTESIS = (
    "Al pasar un término con paréntesis al otro lado, cambia el signo de todo lo que tiene "
    "dentro, no solo el del primer término."
)

# Propiedad distributiva: la plantilla de la taxonomía ("multiplicar {factor} por cada término dentro
# del paréntesis, no solo por el primero") solo describe el error de omitir un término; el diagnóstico
# distingue más variantes y cada una tiene su pista.
PISTAS_DISTRIBUTIVA = {
    "signo": "Al multiplicar {factor} por cada término del paréntesis, revisa el signo de cada resultado.",
    "suma_factor": "La propiedad distributiva pide multiplicar, no sumar: multiplica {factor} por cada término del paréntesis.",
    "suma_magnitudes": "La propiedad distributiva pide multiplicar, no sumar: multiplica {factor} por cada término del paréntesis.",
    "agrega_incognita": "Al multiplicar {factor} por un número, el resultado no lleva x: la x solo aparece si el término que multiplicas ya la tenía.",
    "pierde_incognita": "Al multiplicar {factor} por un término que tiene x, el resultado también tiene x: revisa que no se haya perdido.",
    "parentesis_con_mas": "Cuando el paréntesis tiene un + delante, al quitarlo los signos de adentro no cambian.",
    "factor_doble": "Revisa que el {factor} multiplique a cada término una sola vez.",
    "termino_externo": "El {factor} solo multiplica lo que está dentro del paréntesis: los términos que quedan fuera no se multiplican.",
    "factor_repetido_afuera": "Después de multiplicar {factor} por cada término del paréntesis, el {factor} ya no debe quedar escrito afuera.",
    "un_termino_del_factor": "Al multiplicar dos paréntesis, cada término de uno debe multiplicar a cada término del otro.",
}

PLANTILLA_DIVISION_FACTOR = (
    "Para quitar el {coeficiente} que multiplica al paréntesis, debes dividir ambos lados entre {coeficiente}."
)
PLANTILLA_DIVISION_SUMA = (
    "Para despejar la incógnita, debes dividir ambos lados entre todo el coeficiente que la acompaña, "
    "en este caso ({coeficiente}), no solo entre uno de sus términos."
)
PLANTILLA_ARITMETICA_LADO = (
    "Revisa el cálculo numérico del lado {lado}: la operación que aplicaste es correcta, "
    "pero el resultado no lo es."
)
PLANTILLA_UN_LADO = (
    "{operacion} solo en el lado {lado}, pero cualquier operación que realices debe aplicarse a "
    "ambos lados de la ecuación para mantener la igualdad."
)
_VERBOS_UN_LADO = {"restó": "Restaste", "sumó": "Sumaste",
                   "multiplicó por": "Multiplicaste por", "dividió entre": "Dividiste entre"}
_UN_LADO = re.compile(r"^(restó|sumó|multiplicó por|dividió entre) (\d+(?:\.\d+)?) solo en el lado (izquierdo|derecho)$")

# Variable de cada plantilla -> clave de ResultadoDiagnostico.detalles
_CAMPOS = {
    "{termino}": "termino",
    "{factor}": "factor",
    "{coeficiente}": "coeficiente",
}


def _como_decimal(valor: str) -> str:
    """'1/2' -> '0.5' cuando la fracción tiene expansión decimal finita; si no, se deja igual.

    El diagnóstico guarda el coeficiente como racional exacto, pero solo llega fraccionario
    cuando el estudiante lo escribió como decimal (0.5x = 3); se le muestra como lo escribió.
    """
    if "/" not in valor:
        return valor
    try:
        f = Fraction(valor)
    except (ValueError, ZeroDivisionError):
        return valor
    den = f.denominator
    for primo in (2, 5):
        while den % primo == 0:
            den //= primo
    if den != 1:
        return valor
    texto = f"{float(f):.10f}".rstrip("0").rstrip(".")
    return texto


def _como_se_escribe(valor: str) -> str:
    """SymPy escribe 6*x; el estudiante escribe 6x."""
    return re.sub(r"(\d)\*([A-Za-z(])", r"\1\2", valor)


def _rellenar(plantilla: str, detalles: dict) -> str | None:
    """Rellena los marcadores; devuelve None si falta algún dato."""
    for marcador, clave in _CAMPOS.items():
        if marcador in plantilla:
            valor = str(detalles.get(clave, "")).strip()
            if not valor:
                return None
            if clave == "coeficiente":
                valor = _como_decimal(valor)
            plantilla = plantilla.replace(marcador, _como_se_escribe(valor))
    return plantilla


def _terminos_por_lado(texto: str):
    """Términos de cada lado de la ecuación escrita: {clave (|coeficiente|, resto): [(lado, signo)]}."""
    izq, der = parsear_ecuacion(texto)
    posiciones: dict = {}
    for lado, expr in (("izq", izq), ("der", der)):
        for t in sp.Add.make_args(expr):
            c, resto = sp.sympify(t).doit().as_coeff_Mul()
            c = sp.nsimplify(c)
            if c == 0:
                continue
            posiciones.setdefault((abs(c), resto), []).append((lado, 1 if c > 0 else -1))
    return posiciones


def _situacion_del_signo(termino: str, s_i: str, s_i_mas_1: str) -> str:
    """'mismo_lado' (el término sigue en su lado y se le cambió el signo), 'cambio_de_lado'
    (cambió de lado conservando el signo) u 'otra' si no se puede saber."""
    if not (s_i and s_i_mas_1):
        return "otra"
    try:
        t = sp.sympify(termino, locals={"x": sp.Symbol("x")}).doit()
        if isinstance(t, sp.Add):
            return "otra"
        c, resto = t.as_coeff_Mul()
        c = sp.nsimplify(c)
        clave, signo = (abs(c), resto), (1 if c > 0 else -1)
        antes = _terminos_por_lado(s_i).get(clave, [])
        despues = _terminos_por_lado(s_i_mas_1).get(clave, [])
    except (ErrorDeParseo, sp.SympifyError, TypeError, ValueError):
        return "otra"
    if len(antes) != 1 or len(despues) != 1 or antes[0][1] != signo:
        return "otra"
    (lado0, _), (lado1, signo1) = antes[0], despues[0]
    if lado1 == lado0 and signo1 == -signo:
        return "mismo_lado"
    if lado1 != lado0 and signo1 == signo:
        return "cambio_de_lado"
    return "otra"


def _pista_de_signo(plantilla: str, detalles: dict, s_i: str, s_i_mas_1: str) -> str | None:
    explicacion = str(detalles.get("explicacion", ""))
    if detalles.get("multiplicador") and detalles.get("valor_correcto") and "termino" not in detalles:
        return PLANTILLA_SIGNO_AL_MULTIPLICAR.format(multiplicador=detalles["multiplicador"])
    if "signo opuesto en cada lado" in explicacion:
        return _rellenar(PLANTILLA_SIGNO_OPERACION_OPUESTA, detalles)
    if "además le cambió el signo" in explicacion:
        return PLANTILLA_SIGNO_PARENTESIS
    termino = str(detalles.get("termino", "")).strip()
    if not termino:
        return None
    situacion = _situacion_del_signo(termino, s_i, s_i_mas_1)
    if situacion == "cambio_de_lado":
        return _rellenar(plantilla, detalles)          # plantilla de la taxonomía
    if situacion == "mismo_lado":
        return _rellenar(PLANTILLA_SIGNO_MISMO_LADO, detalles)
    return PLANTILLA_SIGNO_NEUTRA


def _pista_distributiva(plantilla: str, detalles: dict) -> str | None:
    especifica = PISTAS_DISTRIBUTIVA.get(detalles.get("variante", ""))
    if especifica is None:
        return _rellenar(plantilla, detalles)
    factor = str(detalles.get("factor", "")).strip()
    if "{factor}" in especifica and not factor:
        return None
    return especifica.replace("{factor}", _como_se_escribe(factor))


def _pista_division(plantilla: str, detalles: dict) -> str | None:
    explicacion = str(detalles.get("explicacion", ""))
    coeficiente = _como_decimal(str(detalles.get("coeficiente", "")).strip())
    if not coeficiente:
        return None
    if explicacion.startswith("para quitar el factor"):
        return PLANTILLA_DIVISION_FACTOR.replace("{coeficiente}", coeficiente)
    if re.search(r"(?<!^)[+\-]|\(", coeficiente):     # el coeficiente es una suma: (5 - 2)x
        return PLANTILLA_DIVISION_SUMA.replace("{coeficiente}", coeficiente)
    return _rellenar(plantilla, detalles)


def _pista_aritmetica(plantilla: str, detalles: dict) -> str:
    lado = detalles.get("lado")
    if lado in ("izquierdo", "derecho"):
        return PLANTILLA_ARITMETICA_LADO.replace("{lado}", lado)
    return plantilla


def _pista_un_lado(plantilla: str, detalles: dict) -> str:
    m = _UN_LADO.match(str(detalles.get("explicacion", "")))
    if not m:
        return plantilla
    verbo, numero, lado = m.groups()
    return PLANTILLA_UN_LADO.replace("{operacion}", f"{_VERBOS_UN_LADO[verbo]} {numero}").replace("{lado}", lado)


def generar_retroalimentacion_plantilla(resultado: ResultadoDiagnostico, s_i: str = "",
                                        s_i_mas_1: str = "") -> str:
    categoria = obtener_categoria(resultado.categoria_id)
    plantilla = categoria["plantilla_referencia"]
    if plantilla is None:
        return MENSAJE_GENERAL
    detalles = resultado.detalles or {}
    if resultado.categoria_id == "error_signo":
        texto = _pista_de_signo(plantilla, detalles, s_i, s_i_mas_1)
    elif resultado.categoria_id == "distributiva_incorrecta":
        texto = _pista_distributiva(plantilla, detalles)
    elif resultado.categoria_id == "division_coeficiente_equivocado":
        texto = _pista_division(plantilla, detalles)
    elif resultado.categoria_id == "simplificacion_aritmetica":
        texto = _pista_aritmetica(plantilla, detalles)
    elif resultado.categoria_id == "operacion_un_lado":
        texto = _pista_un_lado(plantilla, detalles)
    else:
        texto = _rellenar(plantilla, detalles)
    if texto is None:
        return MENSAJE_GENERAL
    return _como_lo_escribio(texto, s_i + " " + s_i_mas_1)


def _como_lo_escribio(texto: str, pasos: str) -> str:
    """Si el estudiante escribió decimales (1.5), las fracciones de la pista se muestran como decimal (3/2 -> 1.5)."""
    if not re.search(r"\d\.\d", pasos):
        return texto
    return re.sub(r"(?<![\w./])\d+/\d+(?![\w./])", lambda m: _como_decimal(m.group(0)), texto)
