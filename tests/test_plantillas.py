"""Pruebas del generador con plantillas. Los ejemplos viven en tests/datos/plantillas.json."""
import json
import re
from pathlib import Path

import pytest

from src.diagnostico.diagnostico import ResultadoDiagnostico, diagnosticar
from src.generador.plantillas import MENSAJE_GENERAL, generar_retroalimentacion_plantilla
from src.verificador.verificador import verificar_paso

CASOS = json.loads((Path(__file__).parent / "datos" / "plantillas.json").read_text(encoding="utf-8"))


def _diagnostico(caso):
    return diagnosticar(verificar_paso(caso["s_i"], caso["s_i_mas_1"]).discrepancia)


@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_texto_esperado(caso):
    resultado = _diagnostico(caso)
    assert resultado.categoria_id == caso["categoria_esperada"]
    assert generar_retroalimentacion_plantilla(resultado) == caso["retroalimentacion_esperada"]


@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_no_quedan_marcadores_sin_rellenar(caso):
    assert not re.search(r"[{}]", generar_retroalimentacion_plantilla(_diagnostico(caso)))


@pytest.mark.parametrize("categoria", ["error_signo", "distributiva_incorrecta", "division_coeficiente_equivocado"])
def test_falta_dato_usa_mensaje_general(categoria):
    resultado = ResultadoDiagnostico(categoria_id=categoria, detalles={})
    assert generar_retroalimentacion_plantilla(resultado) == MENSAJE_GENERAL


def test_indeterminado_mensaje_general():
    resultado = ResultadoDiagnostico(categoria_id="indeterminado", detalles={})
    assert generar_retroalimentacion_plantilla(resultado) == MENSAJE_GENERAL
