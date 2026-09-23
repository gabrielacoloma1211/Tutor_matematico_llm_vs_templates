"""
Módulo de diagnóstico determinista.

Responsabilidad única: recibir la discrepancia simbólica reportada por el
verificador y clasificarla en una de las categorías de la taxonomía de
errores, mediante un árbol de decisión. Este módulo NO decide si un paso es
válido (eso ya lo resolvió el verificador) ni genera ninguna retroalimentación
en lenguaje natural (eso lo hace el generador).

TODO: implementar el árbol de decisión completo. Esta versión
inicial solo define la interfaz y dos reglas simples (error de signo con un
único término, y "indeterminado" como categoría de reserva) a modo de ejemplo.
"""
import json
from dataclasses import dataclass
from pathlib import Path

import sympy as sp

from src.verificador.verificador import Discrepancia

_RUTA_TAXONOMIA = Path(__file__).resolve().parent.parent.parent / "data" / "taxonomia.json"


@dataclass
class ResultadoDiagnostico:
    categoria_id: str
    detalles: dict


def _cargar_taxonomia() -> dict:
    with open(_RUTA_TAXONOMIA, encoding="utf-8") as f:
        return json.load(f)


TAXONOMIA = _cargar_taxonomia()


def _es_error_de_signo(discrepancia: Discrepancia) -> bool:
    """
    Regla de ejemplo: si la diferencia entre las formas normalizadas de S_i y
    S_{i+1} es, salvo el signo, un único término (es decir, la diferencia
    tiene un solo monomio no nulo), es muy probable que se trate de un error
    de signo en la transposición de ese término.

    NOTA: esta es una primera aproximación ingenua. Falta diferenciarla con
    precisión de los otros tipos de error (por ejemplo, distinguirla del caso
    de "operación realizada en un solo lado", que también puede producir una
    diferencia de un solo término). Ese refinamiento queda pendiente para la
    semana 5-6, cuando se implemente el árbol de decisión completo.
    """
    diferencia = sp.sympify(discrepancia.diferencia)
    diferencia_expandida = sp.expand(diferencia)
    terminos = sp.Add.make_args(diferencia_expandida)
    return len(terminos) == 1


def diagnosticar(discrepancia: Discrepancia) -> ResultadoDiagnostico:
    """
    Punto de entrada del módulo de diagnóstico. Recibe la discrepancia
    reportada por el verificador (ver src/verificador/verificador.py) y
    devuelve la categoría de error correspondiente según la taxonomía.
    """
    # TODO: implementar aquí el árbol de decisión completo, cubriendo las
    # cinco categorías (ver data/taxonomia.json) en el orden adecuado:
    #   1. ¿La discrepancia involucra un paréntesis en S_i? -> distributiva_incorrecta
    #   2. ¿Cambió un lado completo sin modificar el otro? -> operacion_un_lado
    #   3. ¿La operación es correcta pero el número no? -> simplificacion_aritmetica
    #   4. ¿El paso final de despeje usa un divisor incorrecto? -> division_coeficiente_equivocado
    #   5. ¿Es un solo término con signo invertido? -> error_signo
    #   6. Si ninguna regla aplica con claridad -> indeterminado

    if _es_error_de_signo(discrepancia):
        return ResultadoDiagnostico(
            categoria_id="error_signo",
            detalles={"diferencia": discrepancia.diferencia},
        )

    return ResultadoDiagnostico(
        categoria_id="indeterminado",
        detalles={"diferencia": discrepancia.diferencia},
    )


def obtener_categoria(categoria_id: str) -> dict:
    """Devuelve la información completa de una categoría a partir de su id."""
    for categoria in TAXONOMIA["categorias"]:
        if categoria["id"] == categoria_id:
            return categoria
    raise ValueError(f"Categoría desconocida: {categoria_id}")
