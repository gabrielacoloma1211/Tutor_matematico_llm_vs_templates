"""Generador de retroalimentación con plantillas contextualizadas.

Toma el resultado del diagnóstico y rellena la plantilla de la categoría con
los datos del paso del estudiante (término, factor, coeficiente). No usa LLM:
es determinista y no inventa contenido.
"""
import json
import re
from fractions import Fraction
from pathlib import Path

import sympy as sp

from src.diagnostico.diagnostico import ResultadoDiagnostico, obtener_categoria
from src.verificador.verificador import ErrorDeParseo, parsear_ecuacion

# Los textos de las pistas no están en el código: viven en data/plantillas.json (igual que las
# plantillas de la taxonomía en data/taxonomia.json), para poder revisarlos y cambiarlos sin tocar el programa.
RUTA_TEXTOS = Path(__file__).resolve().parents[2] / "data" / "plantillas.json"


def cargar_textos() -> dict:
    with open(RUTA_TEXTOS, encoding="utf-8") as f:
        return json.load(f)


TEXTOS = cargar_textos()

MENSAJE_GENERAL = TEXTOS["mensaje_general"]

# El diagnóstico llama error_signo a varias situaciones y la plantilla de la taxonomía ("al moverlo
# al otro lado, su signo debe cambiar") solo describe una. Según cómo escribió el estudiante el
# término, se elige entre estas pistas; ninguna dice que el término cambió de lado si no lo hizo.
PLANTILLA_SIGNO_MISMO_LADO = TEXTOS["signo"]["mismo_lado"]
PLANTILLA_SIGNO_NEUTRA = TEXTOS["signo"]["neutra"]
PLANTILLA_SIGNO_AL_MULTIPLICAR = TEXTOS["signo"]["al_multiplicar"]
PLANTILLA_SIGNO_OPERACION_OPUESTA = TEXTOS["signo"]["operacion_opuesta"]
PLANTILLA_SIGNO_PARENTESIS = TEXTOS["signo"]["parentesis"]

# Propiedad distributiva: la plantilla de la taxonomía ("multiplicar {factor} por cada término dentro
# del paréntesis, no solo por el primero") solo describe el error de omitir un término; el diagnóstico
# distingue más variantes y cada una tiene su pista.
PISTAS_DISTRIBUTIVA = TEXTOS["distributiva"]

PLANTILLA_DIVISION_FACTOR = TEXTOS["division"]["factor"]
PLANTILLA_DIVISION_SUMA = TEXTOS["division"]["suma"]
PLANTILLA_ARITMETICA_LADO = TEXTOS["aritmetica"]["lado"]
PLANTILLA_UN_LADO = TEXTOS["un_lado"]["plantilla"]
_VERBOS_UN_LADO = TEXTOS["un_lado"]["verbos"]
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
