"""
Pruebas del verificador matemático, usando los mismos ejemplos definidos en
la taxonomía de errores del proyecto.

Los ejemplos (pasos válidos, pasos inválidos y ecuaciones mal escritas) están
en tests/datos/verificador.json.
"""
import pytest

from src.verificador.verificador import verificar_paso, parsear_ecuacion, ErrorDeParseo
from tests.datos import cargar

DATOS = cargar("verificador")
PASOS = DATOS["pasos"]
PASOS_VALIDOS = [p for p in PASOS if p["valido"]]
PASOS_INVALIDOS = [p for p in PASOS if not p["valido"]]
ECUACIONES_MAL_ESCRITAS = DATOS["ecuaciones_mal_escritas"]


def _ids(lista):
    return [p["id"] for p in lista]


@pytest.mark.parametrize("paso", PASOS_VALIDOS, ids=_ids(PASOS_VALIDOS))
def test_un_paso_valido_no_genera_discrepancia(paso):
    r = verificar_paso(paso["s_i"], paso["s_i_mas_1"])
    assert r.valido is True
    assert r.discrepancia is None


@pytest.mark.parametrize("paso", PASOS_INVALIDOS, ids=_ids(PASOS_INVALIDOS))
def test_un_paso_invalido_genera_discrepancia(paso):
    r = verificar_paso(paso["s_i"], paso["s_i_mas_1"])
    assert r.valido is False
    assert r.discrepancia is not None


@pytest.mark.parametrize("entrada", ECUACIONES_MAL_ESCRITAS, ids=_ids(ECUACIONES_MAL_ESCRITAS))
def test_una_ecuacion_mal_escrita_lanza_error_de_parseo(entrada):
    with pytest.raises(ErrorDeParseo):
        parsear_ecuacion(entrada["ecuacion"])
