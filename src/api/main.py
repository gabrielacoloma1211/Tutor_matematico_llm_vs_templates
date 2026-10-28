"""
Backend FastAPI del tutor matemático.

Expone el pipeline verificador -> diagnóstico -> generador de retroalimentación. El
estudiante elige si la pista la redacta el LLM o una plantilla (`modo`); el verificador y
el diagnóstico son los mismos en ambos casos. También sirve la interfaz web en `/`.
"""
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import sympy as sp

from src.verificador.verificador import verificar_paso, parsear_ecuacion, ErrorDeParseo
from src.diagnostico.diagnostico import diagnosticar, obtener_categoria
from src.generador import llm as generador_llm
from src.generador.plantillas import generar_retroalimentacion_plantilla

INTERFAZ = Path(__file__).parent / "static" / "index.html"

app = FastAPI(
    title="Tutor Matemático — API",
    description="Verificación simbólica y diagnóstico de errores en ecuaciones de primer grado.",
    version="0.1.0",
)


class PasoRequest(BaseModel):
    # tope de tamaño antes de procesar nada; el límite fino lo aplica validar_ecuacion
    s_i: str = Field(max_length=1000)
    s_i_mas_1: str = Field(max_length=1000)
    modo: Literal["plantilla", "llm"] = "plantilla"


class PasoResponse(BaseModel):
    valido: bool
    categoria_id: str | None = None
    categoria_nombre: str | None = None
    discrepancia: dict | None = None
    pista: str | None = None
    modo: str | None = None
    generacion: dict | None = None   # latencia y, con LLM, modelo y tokens


def _solucion_es_cero(ecuacion: str) -> bool:
    """True si la ecuación no tiene término numérico suelto (a·x = b·x): su única solución es x = 0.

    Con esas ecuaciones el criterio "misma solución" no distingue un paso correcto de uno
    incorrecto (3x/2 = 5x y 3x = 5x tienen la misma solución), así que quedan fuera del alcance
    del prototipo. La comprobación está aquí y no en el verificador para no alterar el código
    con el que se midió el diagnóstico.
    """
    izq, der = parsear_ecuacion(ecuacion)
    diferencia = sp.expand(izq - der)
    return diferencia != 0 and diferencia.subs(sp.Symbol("x"), 0) == 0


@app.get("/", include_in_schema=False)
def interfaz():
    """Interfaz web del estudiante."""
    return FileResponse(INTERFAZ)


@app.get("/salud")
def salud():
    """Endpoint simple para confirmar que el servidor está corriendo."""
    return {"estado": "ok"}


@app.post("/verificar", response_model=PasoResponse)
def verificar(paso: PasoRequest):
    """
    Recibe un paso de un estudiante (S_i -> S_{i+1}) y devuelve si es válido;
    si no lo es, incluye además la categoría de error diagnosticada.

    Si alguna de las dos ecuaciones no se puede interpretar (por ejemplo "3x + = 7"),
    responde HTTP 422 con un error de formato. `valido=False` queda reservado para
    pasos que se procesaron bien pero cuya transformación algebraica es incorrecta.
    """
    try:
        if _solucion_es_cero(paso.s_i):
            raise ErrorDeParseo(
                "Por ahora no reviso ecuaciones cuya solución es x = 0 (las que no tienen un número "
                "suelto, como 2x = 5x), porque no puedo distinguir un paso correcto de uno incorrecto. "
                "Prueba con otra ecuación.",
                tipo="entrada_no_permitida",
            )
        resultado_verificacion = verificar_paso(paso.s_i, paso.s_i_mas_1)
    except ErrorDeParseo as e:
        raise HTTPException(
            status_code=422,
            detail={"tipo": e.tipo, "mensaje": str(e)},
        ) from e

    if resultado_verificacion.valido:
        return PasoResponse(valido=True)

    resultado_diagnostico = diagnosticar(resultado_verificacion.discrepancia)
    categoria = obtener_categoria(resultado_diagnostico.categoria_id)

    if paso.modo == "llm":
        try:
            g = generador_llm.generar_retroalimentacion_llm(
                resultado_diagnostico, paso.s_i, paso.s_i_mas_1)
        except generador_llm.LLMNoDisponible as e:
            raise HTTPException(
                status_code=503,
                detail={"tipo": "llm_no_disponible", "mensaje": str(e)},
            ) from e
        pista = g.texto
        generacion = {"latencia_ms": round(g.latencia_ms, 1), "usado_llm": g.usado_llm,
                      "modelo": g.modelo, "tokens_entrada": g.tokens_entrada,
                      "tokens_salida": g.tokens_salida}
    else:
        inicio = time.perf_counter()
        pista = generar_retroalimentacion_plantilla(resultado_diagnostico)
        generacion = {"latencia_ms": round((time.perf_counter() - inicio) * 1000, 3),
                      "usado_llm": False}

    return PasoResponse(
        valido=False,
        categoria_id=categoria["id"],
        categoria_nombre=categoria["nombre"],
        discrepancia=resultado_diagnostico.detalles,
        pista=pista,
        modo=paso.modo,
        generacion=generacion,
    )
