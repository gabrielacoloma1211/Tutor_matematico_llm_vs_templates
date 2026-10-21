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
