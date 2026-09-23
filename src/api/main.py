"""
Backend FastAPI del tutor matemático.

Expone el pipeline verificador -> diagnóstico. La generación de
retroalimentación (con LLM o con plantilla) se conectará aquí, 
una vez implementados ambos componentes.
"""
from fastapi import FastAPI
from pydantic import BaseModel

from src.verificador.verificador import verificar_paso, ErrorDeParseo
from src.diagnostico.diagnostico import diagnosticar, obtener_categoria

app = FastAPI(
    title="Tutor Matemático — API",
    description="Verificación simbólica y diagnóstico de errores en ecuaciones de primer grado.",
    version="0.1.0",
)


class PasoRequest(BaseModel):
    s_i: str
    s_i_mas_1: str


class PasoResponse(BaseModel):
    valido: bool
    categoria_id: str | None = None
    categoria_nombre: str | None = None
    discrepancia: dict | None = None


@app.get("/salud")
def salud():
    """Endpoint simple para confirmar que el servidor está corriendo."""
    return {"estado": "ok"}


@app.post("/verificar", response_model=PasoResponse)
def verificar(paso: PasoRequest):
    """
    Recibe un paso de un estudiante (S_i -> S_{i+1}) y devuelve si es válido;
    si no lo es, incluye además la categoría de error diagnosticada.
    """
    try:
        resultado_verificacion = verificar_paso(paso.s_i, paso.s_i_mas_1)
    except ErrorDeParseo as e:
        return PasoResponse(valido=False, discrepancia={"error_de_parseo": str(e)})

    if resultado_verificacion.valido:
        return PasoResponse(valido=True)

    resultado_diagnostico = diagnosticar(resultado_verificacion.discrepancia)
    categoria = obtener_categoria(resultado_diagnostico.categoria_id)

    return PasoResponse(
        valido=False,
        categoria_id=categoria["id"],
        categoria_nombre=categoria["nombre"],
        discrepancia=resultado_diagnostico.detalles,
    )
