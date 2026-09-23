"""
Generador de retroalimentación — arquitectura propuesta (con LLM).

Responsabilidad única: dado el resultado del diagnóstico (ya resuelto y
verificado de forma determinista), redactar una pista pedagógica en lenguaje
natural, adaptada al nivel educativo del estudiante. Este componente NO
participa en la verificación de la corrección matemática ni en la
clasificación del error — solo traduce un diagnóstico ya resuelto a un
lenguaje comprensible.

TODO: implementar la integración real con la API del LLM que se defina. 
Esta versión es un esqueleto con el diseño del
prompt para no perder la idea antes de implementarlo.
"""
import os

from src.diagnostico.diagnostico import ResultadoDiagnostico, obtener_categoria

PROMPT_SISTEMA = """\
Eres un tutor de matemáticas para estudiantes de noveno año de Educación General Básica \
en Ecuador. Un estudiante cometió un error al resolver una ecuación de primer grado con \
una incógnita. Ya se determinó, de forma exacta y verificada, que el error corresponde a \
la categoría: "{nombre_categoria}" ({definicion_categoria}).

Tu única tarea es redactar una pista breve (2-3 líneas) que ayude al estudiante a \
identificar y corregir su error por sí mismo. No le des la solución completa. No repitas \
información que el estudiante ya puede ver en su propio trabajo. Usa un tono cercano y \
alentador, apropiado para un estudiante de 13-14 años.
"""


def _construir_prompt(resultado: ResultadoDiagnostico) -> str:
    categoria = obtener_categoria(resultado.categoria_id)
    return PROMPT_SISTEMA.format(
        nombre_categoria=categoria["nombre"],
        definicion_categoria=categoria["definicion"],
    )


def generar_retroalimentacion_llm(resultado: ResultadoDiagnostico) -> str:
    """
    Genera la retroalimentación para el estudiante usando un LLM, a partir
    del diagnóstico ya resuelto.
    """
    # TODO: reemplazar por la llamada real, por ejemplo con el SDK de Anthropic:
    #
    # from anthropic import Anthropic
    # client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    # respuesta = client.messages.create(
    #     model="claude-sonnet-4-5",
    #     max_tokens=200,
    #     system=_construir_prompt(resultado),
    #     messages=[{"role": "user", "content": "Genera la pista para el estudiante."}],
    # )
    # return respuesta.content[0].text

    raise NotImplementedError(
        "La integración con el LLM todavía no está implementada. "
        "Ver TODO en src/generador/llm.py (planificado para semana 8-9)."
    )
