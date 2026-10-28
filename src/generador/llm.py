"""
Generador de retroalimentación con LLM.

Responsabilidad única: dado el resultado del diagnóstico (ya resuelto y verificado de
forma determinista), redactar una pista pedagógica en lenguaje natural para un estudiante
de noveno de EGB. Este componente NO participa en la verificación de la corrección
matemática ni en la clasificación del error.

Decisiones de diseño (a justificar en la tesis):
- El cliente de la API se puede inyectar, así las pruebas no llaman al servicio real.
- Cada llamada devuelve también la latencia y los tokens usados (para la sección de costos).
- Si el diagnóstico es `indeterminado` no se llama al LLM y se devuelve el mismo mensaje
  general de la versión con plantillas, hasta que el tutor decida otra cosa
  (LLAMAR_EN_INDETERMINADO).
- Parámetros fijos y baja temperatura, para que la comparación sea lo más reproducible posible.
"""
import os
import time
from dataclasses import dataclass

from src.diagnostico.diagnostico import ResultadoDiagnostico, obtener_categoria
from src.generador.plantillas import MENSAJE_GENERAL

MODELO = os.environ.get("TUTOR_MODELO_LLM", "claude-sonnet-5-5")
TEMPERATURA = 0.2
MAX_TOKENS = 200
TIMEOUT_SEGUNDOS = 20.0
LLAMAR_EN_INDETERMINADO = False

PROMPT_SISTEMA = """\
Eres un tutor de matemáticas para estudiantes de noveno año de Educación General Básica \
en Ecuador. Un estudiante cometió un error al resolver una ecuación de primer grado con \
una incógnita. Ya se determinó, de forma exacta y verificada, que el error corresponde a \
la categoría: "{nombre_categoria}" ({definicion_categoria}).

Tu única tarea es redactar una pista breve (2-3 líneas) que ayude al estudiante a \
identificar y corregir su error por sí mismo. No le des la solución completa ni escribas \
la ecuación corregida. No cambies la categoría del error ni hagas tu propia verificación \
matemática: confía en el diagnóstico. No repitas información que el estudiante ya puede ver \
en su propio trabajo. Usa un tono cercano y alentador, apropiado para un estudiante de \
13-14 años. Responde solo con la pista, en español.
"""

# Datos del diagnóstico que se le pasan al LLM (los mismos tipos de dato que usan las plantillas,
# más la explicación del error). `diferencia` es una expresión algebraica para uso interno.
_DATOS_UTILES = ("termino", "factor", "coeficiente", "divisor_usado", "multiplicador",
                 "valor_correcto", "valor_escrito", "explicacion")


class LLMNoDisponible(Exception):
    """No hay clave de API, el paquete no está instalado o el servicio falló."""


@dataclass
class RespuestaGenerador:
    texto: str
    modo: str                    # "llm" o "plantilla"
    usado_llm: bool
    latencia_ms: float
    modelo: str | None = None
    tokens_entrada: int | None = None
    tokens_salida: int | None = None


def _construir_prompt(resultado: ResultadoDiagnostico) -> str:
    categoria = obtener_categoria(resultado.categoria_id)
    return PROMPT_SISTEMA.format(
        nombre_categoria=categoria["nombre"],
        definicion_categoria=categoria["definicion"],
    )


def _construir_mensaje_usuario(resultado: ResultadoDiagnostico, s_i: str, s_i_mas_1: str) -> str:
    lineas = []
    if s_i and s_i_mas_1:
        lineas.append(f"Paso anterior del estudiante: {s_i}")
        lineas.append(f"Paso que escribió el estudiante: {s_i_mas_1}")
    datos = {k: v for k, v in (resultado.detalles or {}).items()
             if k in _DATOS_UTILES and str(v).strip()}
    if datos:
        lineas.append("Datos del diagnóstico: " + "; ".join(f"{k} = {v}" for k, v in datos.items()))
    lineas.append("Escribe la pista para el estudiante.")
    return "\n".join(lineas)


def _crear_cliente():
    clave = os.environ.get("ANTHROPIC_API_KEY")
    if not clave:
        raise LLMNoDisponible("Falta la variable de entorno ANTHROPIC_API_KEY.")
    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise LLMNoDisponible("El paquete 'anthropic' no está instalado.") from e
    return Anthropic(api_key=clave, timeout=TIMEOUT_SEGUNDOS, max_retries=1)


def generar_retroalimentacion_llm(resultado: ResultadoDiagnostico, s_i: str = "",
                                  s_i_mas_1: str = "", cliente=None) -> RespuestaGenerador:
    """Redacta la pista con el LLM. `cliente` permite inyectar uno falso en las pruebas."""
    inicio = time.perf_counter()
    if resultado.categoria_id == "indeterminado" and not LLAMAR_EN_INDETERMINADO:
        return RespuestaGenerador(MENSAJE_GENERAL, "llm", False, (time.perf_counter() - inicio) * 1000)

    if cliente is None:
        cliente = _crear_cliente()
    try:
        respuesta = cliente.messages.create(
            model=MODELO,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURA,
            system=_construir_prompt(resultado),
            messages=[{"role": "user",
                       "content": _construir_mensaje_usuario(resultado, s_i, s_i_mas_1)}],
        )
    except Exception as e:  # fallo de red, de cuota o del servicio
        raise LLMNoDisponible(f"El servicio del LLM no respondió: {type(e).__name__}") from e

    texto = "".join(getattr(b, "text", "") for b in respuesta.content).strip()
    if not texto:
        raise LLMNoDisponible("El LLM devolvió una respuesta vacía.")
    uso = getattr(respuesta, "usage", None)
    return RespuestaGenerador(
        texto=texto, modo="llm", usado_llm=True,
        latencia_ms=(time.perf_counter() - inicio) * 1000, modelo=MODELO,
        tokens_entrada=getattr(uso, "input_tokens", None),
        tokens_salida=getattr(uso, "output_tokens", None),
    )
