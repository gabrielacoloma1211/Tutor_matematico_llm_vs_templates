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
- Parámetros fijos (la temperatura no se envía: los modelos 5.x la rechazan), para que la comparación sea lo más reproducible posible.
"""
import os
import time
from dataclasses import dataclass
from pathlib import Path

RUTA_ENV = Path(__file__).resolve().parents[2] / ".env"


def _cargar_env(ruta: Path = RUTA_ENV) -> None:
    """Lee las líneas CLAVE=valor de un archivo .env (no se sube a Git). Una variable ya definida en el entorno tiene prioridad."""
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8-sig").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        nombre, valor = linea.split("=", 1)
        nombre = nombre.strip().removeprefix("export ").strip()
        valor = valor.strip().strip('"').strip("'")
        if nombre and valor:
            os.environ.setdefault(nombre, valor)


_cargar_env()

from src.diagnostico.diagnostico import ResultadoDiagnostico, obtener_categoria
from src.generador.plantillas import MENSAJE_GENERAL, RUTA_TEXTOS

MODELO = os.environ.get("TUTOR_MODELO_LLM", "claude-haiku-5-5")
# Los modelos 5.x rechazan `temperature` (error 400: deprecated). None = no se envía; se usa el valor por defecto del modelo.
TEMPERATURA = None
# Los modelos 5.x razonan antes de responder y ese razonamiento cuenta como salida: con 200 la respuesta salía vacía o cortada.
MAX_TOKENS = 4096
TIMEOUT_SEGUNDOS = 20.0
LLAMAR_EN_INDETERMINADO = False

# El prompt no está en el código: vive en data/prompt_llm.txt (con los marcadores {nombre_categoria}
# y {definicion_categoria}, que se rellenan con la categoría del diagnóstico).
RUTA_PROMPT = RUTA_TEXTOS.with_name("prompt_llm.txt")
PROMPT_SISTEMA = RUTA_PROMPT.read_text(encoding="utf-8")

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
    motivo_fin: str | None = None   # stop_reason del API ("max_tokens" = pista cortada)
    tipos_bloque: tuple = ()        # tipos de bloque devueltos (p. ej. text, thinking)


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
        raise LLMNoDisponible(
            "Falta la variable de entorno ANTHROPIC_API_KEY "
            f"(no está en el entorno y {'el archivo .env está vacío o no tiene esa línea' if RUTA_ENV.is_file() else 'no existe el archivo ' + str(RUTA_ENV)}).")
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
        parametros = {}
        if TEMPERATURA is not None:
            parametros["temperature"] = TEMPERATURA
        respuesta = cliente.messages.create(
            model=MODELO,
            max_tokens=MAX_TOKENS,
            system=_construir_prompt(resultado),
            messages=[{"role": "user",
                       "content": _construir_mensaje_usuario(resultado, s_i, s_i_mas_1)}],
            **parametros,
        )
    except Exception as e:  # fallo de red, de cuota o del servicio
        raise LLMNoDisponible(f"El servicio del LLM no respondió: {type(e).__name__}") from e

    bloques = list(respuesta.content)
    texto = "".join((getattr(b, "text", None) or "") for b in bloques
                    if getattr(b, "type", "text") == "text").strip()
    if not texto:
        uso_ = getattr(respuesta, "usage", None)
        raise LLMNoDisponible(
            "El LLM devolvió una respuesta vacía "
            f"(fin={getattr(respuesta, 'stop_reason', None)}, "
            f"bloques={[getattr(b, 'type', '?') for b in bloques]}, "
            f"tokens_salida={getattr(uso_, 'output_tokens', None)}, max_tokens={MAX_TOKENS}).")
    uso = getattr(respuesta, "usage", None)
    return RespuestaGenerador(
        texto=texto, modo="llm", usado_llm=True,
        latencia_ms=(time.perf_counter() - inicio) * 1000, modelo=MODELO,
        tokens_entrada=getattr(uso, "input_tokens", None),
        tokens_salida=getattr(uso, "output_tokens", None),
        motivo_fin=getattr(respuesta, "stop_reason", None),
        tipos_bloque=tuple(getattr(b, "type", "text") for b in bloques),
    )
