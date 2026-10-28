"""
Pruebas del endpoint /verificar.

Una entrada que no se puede interpretar (por ejemplo, una ecuación mal escrita) es un
error de formato: la API responde HTTP 422 y no hace ningún diagnóstico matemático.
`valido=False` se reserva para pasos que se procesaron bien pero cuya transformación
algebraica es incorrecta. Los ejemplos están en tests/datos/api.json.
"""
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from tests.datos import cargar

DATOS = cargar("api")
MAL_ESCRITAS = DATOS["entradas_mal_escritas"]
NO_PERMITIDAS = DATOS["entradas_no_permitidas"]
cliente = TestClient(app)


def _post(paso):
    return cliente.post("/verificar", json={"s_i": paso["s_i"], "s_i_mas_1": paso["s_i_mas_1"]})


@pytest.mark.parametrize("entrada", MAL_ESCRITAS, ids=[e["id"] for e in MAL_ESCRITAS])
def test_una_entrada_mal_escrita_responde_422_y_no_un_diagnostico(entrada):
    r = _post(entrada)
    assert r.status_code == 422
    cuerpo = r.json()
    assert cuerpo["detail"]["tipo"] == "error_de_formato"
    assert cuerpo["detail"]["mensaje"]
    assert "valido" not in cuerpo
    assert "categoria_id" not in cuerpo


@pytest.mark.parametrize("entrada", NO_PERMITIDAS, ids=[e["id"] for e in NO_PERMITIDAS])
def test_una_entrada_no_autorizada_responde_422_y_se_rechaza(entrada):
    r = _post(entrada)
    assert r.status_code == 422
    cuerpo = r.json()
    assert "valido" not in cuerpo
    assert "categoria_id" not in cuerpo
    if isinstance(cuerpo["detail"], dict):       # rechazada por el verificador
        assert cuerpo["detail"]["tipo"] == "entrada_no_permitida"
    # si la rechaza antes FastAPI por tamaño, detail es una lista; también es un 422


def test_un_cuerpo_incompleto_responde_422():
    assert cliente.post("/verificar", json={"s_i": DATOS["paso_valido"]["s_i"]}).status_code == 422


def test_un_paso_valido_responde_200_y_valido_verdadero():
    r = _post(DATOS["paso_valido"])
    assert r.status_code == 200
    assert r.json()["valido"] is True


def test_un_paso_matematicamente_incorrecto_responde_200_con_diagnostico():
    r = _post(DATOS["paso_invalido"])
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["valido"] is False
    assert cuerpo["categoria_id"] == DATOS["paso_invalido"]["categoria_id"]


def test_salud():
    assert cliente.get("/salud").json() == {"estado": "ok"}


# ---- generación de la pista (modo plantilla / llm) ----
from types import SimpleNamespace

from src.generador import llm as generador_llm


def _con_modo(paso, modo):
    return cliente.post("/verificar", json={"s_i": paso["s_i"], "s_i_mas_1": paso["s_i_mas_1"], "modo": modo})


def test_por_defecto_la_pista_es_de_plantilla():
    cuerpo = _post(DATOS["paso_invalido"]).json()
    assert cuerpo["modo"] == "plantilla"
    assert cuerpo["pista"] and "{" not in cuerpo["pista"]
    assert cuerpo["generacion"]["usado_llm"] is False


def test_un_paso_valido_no_trae_pista():
    cuerpo = _post(DATOS["paso_valido"]).json()
    assert cuerpo["pista"] is None


def test_un_modo_desconocido_responde_422():
    assert _con_modo(DATOS["paso_invalido"], "otro").status_code == 422


def test_modo_llm_devuelve_la_pista_y_el_registro(monkeypatch):
    falso = SimpleNamespace(texto="Pista de prueba.", usado_llm=True, latencia_ms=812.34,
                            modelo="modelo-falso", tokens_entrada=100, tokens_salida=25)
    monkeypatch.setattr(generador_llm, "generar_retroalimentacion_llm", lambda *a, **k: falso)
    cuerpo = _con_modo(DATOS["paso_invalido"], "llm").json()
    assert cuerpo["modo"] == "llm" and cuerpo["pista"] == "Pista de prueba."
    assert cuerpo["generacion"] == {"latencia_ms": 812.3, "usado_llm": True, "modelo": "modelo-falso",
                                    "tokens_entrada": 100, "tokens_salida": 25}
    assert cuerpo["categoria_id"] == DATOS["paso_invalido"]["categoria_id"]


def test_modo_llm_sin_servicio_responde_503(monkeypatch):
    def falla(*a, **k):
        raise generador_llm.LLMNoDisponible("sin clave")
    monkeypatch.setattr(generador_llm, "generar_retroalimentacion_llm", falla)
    r = _con_modo(DATOS["paso_invalido"], "llm")
    assert r.status_code == 503
    assert r.json()["detail"]["tipo"] == "llm_no_disponible"


def test_la_interfaz_se_sirve_en_la_raiz():
    r = cliente.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]


# ---- ecuaciones con solución x = 0: fuera del alcance (criterio ambiguo) ----
SOLUCION_CERO = DATOS["solucion_cero"]


@pytest.mark.parametrize("entrada", SOLUCION_CERO, ids=[e["id"] for e in SOLUCION_CERO])
def test_una_ecuacion_con_solucion_cero_responde_422(entrada):
    r = _post(entrada)
    assert r.status_code == 422
    assert r.json()["detail"]["tipo"] == "entrada_no_permitida"
    assert "valido" not in r.json()


def test_una_ecuacion_normal_enviada_como_paso_inicial_responde_valido():
    paso = DATOS["paso_valido"]
    assert _post({"s_i": paso["s_i"], "s_i_mas_1": paso["s_i"]}).json()["valido"] is True
