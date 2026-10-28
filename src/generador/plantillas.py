"""Generador de retroalimentación con plantillas contextualizadas.

Toma el resultado del diagnóstico y rellena la plantilla de la categoría con
los datos del paso del estudiante (término, factor, coeficiente). No usa LLM:
es determinista y no inventa contenido.
"""
from fractions import Fraction

from src.diagnostico.diagnostico import ResultadoDiagnostico, obtener_categoria

MENSAJE_GENERAL = (
    "Revisa este paso con más cuidado. No pudimos identificar el tipo exacto de error."
)

# error_signo tiene dos variantes: signo al transponer (trae 'termino') y signo
# perdido al multiplicar toda la ecuación (trae 'multiplicador' y 'valor_correcto').
PLANTILLA_SIGNO_AL_MULTIPLICAR = (
    "Revisa el signo de {valor_correcto}: al multiplicar por {multiplicador}, "
    "el signo del término se conserva."
)

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


def _rellenar(plantilla: str, detalles: dict) -> str | None:
    """Rellena los marcadores; devuelve None si falta algún dato."""
    for marcador, clave in _CAMPOS.items():
        if marcador in plantilla:
            valor = str(detalles.get(clave, "")).strip()
            if not valor:
                return None
            if clave == "coeficiente":
                valor = _como_decimal(valor)
            plantilla = plantilla.replace(marcador, valor)
    return plantilla


def generar_retroalimentacion_plantilla(resultado: ResultadoDiagnostico) -> str:
    categoria = obtener_categoria(resultado.categoria_id)
    plantilla = categoria["plantilla_referencia"]
    if plantilla is None:
        return MENSAJE_GENERAL
    detalles = resultado.detalles or {}

    if (resultado.categoria_id == "error_signo" and "termino" not in detalles
            and detalles.get("multiplicador") and detalles.get("valor_correcto")):
        return PLANTILLA_SIGNO_AL_MULTIPLICAR.format(
            valor_correcto=detalles["valor_correcto"],
            multiplicador=detalles["multiplicador"],
        )

    texto = _rellenar(plantilla, detalles)
    return texto if texto is not None else MENSAJE_GENERAL
