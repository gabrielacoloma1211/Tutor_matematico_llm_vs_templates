"""
Generador de retroalimentación — versión de referencia (sin LLM).

Responsabilidad única: dado el resultado del diagnóstico, rellenar la
plantilla predeterminada correspondiente con los datos específicos del
ejercicio. Este componente es completamente determinista: no usa ningún LLM.

Comparar con src/generador/llm.py, que es la versión de la arquitectura
propuesta (usa un LLM para esta misma tarea).
"""
from src.diagnostico.diagnostico import ResultadoDiagnostico, obtener_categoria


def generar_retroalimentacion_plantilla(resultado: ResultadoDiagnostico) -> str:
    """
    Genera la retroalimentación para el estudiante usando la plantilla
    predeterminada asociada a la categoría diagnosticada.

    TODO: completar el relleno de variables (p. ej. {termino},
    {factor}, {coeficiente}) a partir de los detalles de la discrepancia,
    en vez de dejar la plantilla con las llaves literales.
    """
    categoria = obtener_categoria(resultado.categoria_id)
    plantilla = categoria["plantilla_referencia"]

    if plantilla is None:
        return "Revisa este paso con más cuidado. No pudimos identificar el tipo exacto de error."

    return plantilla
