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
    assert generar_retroalimentacion_plantilla(resultado, caso["s_i"], caso["s_i_mas_1"]) == caso["retroalimentacion_esperada"]


@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_no_quedan_marcadores_sin_rellenar(caso):
    assert not re.search(r"[{}]", generar_retroalimentacion_plantilla(_diagnostico(caso), caso["s_i"], caso["s_i_mas_1"]))


@pytest.mark.parametrize("categoria", ["error_signo", "distributiva_incorrecta", "division_coeficiente_equivocado"])
def test_falta_dato_usa_mensaje_general(categoria):
    resultado = ResultadoDiagnostico(categoria_id=categoria, detalles={})
    assert generar_retroalimentacion_plantilla(resultado) == MENSAJE_GENERAL


def test_indeterminado_mensaje_general():
    resultado = ResultadoDiagnostico(categoria_id="indeterminado", detalles={})
    assert generar_retroalimentacion_plantilla(resultado) == MENSAJE_GENERAL


SIGNO_CON_TERMINO = [c for c in CASOS if c["categoria_esperada"] == "error_signo"]


@pytest.mark.parametrize("caso", SIGNO_CON_TERMINO, ids=[c["id"] for c in SIGNO_CON_TERMINO])
def test_la_pista_de_signo_no_habla_de_cambio_de_lado_si_no_lo_hubo(caso):
    """Sin los pasos escritos no se sabe si el término cambió de lado: la pista no lo afirma."""
    texto = generar_retroalimentacion_plantilla(_diagnostico(caso))
    assert "al moverlo al otro lado" not in texto


def test_cada_variante_de_signo_tiene_una_pista_distinta():
    textos = {c["retroalimentacion_esperada"] for c in SIGNO_CON_TERMINO}
    assert len(textos) >= 5


# ---- revisión sobre todos los casos de desarrollo y del conjunto ampliado ----
import benchmark.validar_casos as _validar
from src.diagnostico.diagnostico import TAXONOMIA


def _todos_los_pasos():
    ampliado = json.loads((Path(_validar.RAIZ) / "benchmark" / "casos" / "ampliado" / "ampliado.json")
                          .read_text(encoding="utf-8"))
    dev = [c for _, c in _validar.cargar_casos(Path(_validar.RAIZ) / "benchmark" / "casos" / "dev")]
    ampliado_2 = json.loads((Path(_validar.RAIZ) / "benchmark" / "casos" / "ampliado_2" / "ampliado_2.json")
                            .read_text(encoding="utf-8"))
    for c in dev + ampliado + ampliado_2:
        k, pasos = c["indice_paso_erroneo"], c["resolucion_estudiante"]
        yield c["id"], pasos[k - 1], pasos[k]


PASOS = list(_todos_los_pasos())


@pytest.mark.parametrize("id_,s_i,s_i1", PASOS, ids=[p[0] for p in PASOS])
def test_ninguna_pista_queda_con_variables_ni_revela_el_valor(id_, s_i, s_i1):
    resultado = diagnosticar(verificar_paso(s_i, s_i1).discrepancia)
    pista = generar_retroalimentacion_plantilla(resultado, s_i, s_i1)
    assert pista and not re.search(r"[{}]", pista)
    valor = str(resultado.detalles.get("valor_correcto", "")).strip()
    if valor:
        assert not re.search(rf"(?<![\d.]){re.escape(valor)}(?![\d.])", pista)
    if resultado.categoria_id != "indeterminado":
        assert pista != MENSAJE_GENERAL


def test_cada_variante_de_la_distributiva_tiene_pista_propia():
    from src.diagnostico.diagnostico import _DESCRIPCION_DISTRIBUTIVA
    from src.generador.plantillas import PISTAS_DISTRIBUTIVA
    faltan = set(_DESCRIPCION_DISTRIBUTIVA) - set(PISTAS_DISTRIBUTIVA) - {"omite_factor"}
    assert not faltan, f"variantes sin pista propia: {sorted(faltan)}"
    assert "un_termino_del_factor" in PISTAS_DISTRIBUTIVA and "factor_repetido_afuera" in PISTAS_DISTRIBUTIVA
