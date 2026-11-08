"""Pruebas del generador con LLM. Usan un cliente falso: nunca llaman al servicio real."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.diagnostico.diagnostico import ResultadoDiagnostico, diagnosticar
from src.generador import llm
from src.generador.plantillas import MENSAJE_GENERAL
from src.verificador.verificador import verificar_paso

CASOS = json.loads((Path(__file__).parent / "datos" / "plantillas.json").read_text(encoding="utf-8"))
CON_CATEGORIA = [c for c in CASOS if c["categoria_esperada"] != "indeterminado"]


class ClienteFalso:
    def __init__(self, texto="Mira el signo de ese término.", falla=None, fin=None):
        self.llamadas = []
        self._texto, self._falla, self._fin = texto, falla, fin
        self.messages = self

    def create(self, **kwargs):
        self.llamadas.append(kwargs)
        if self._falla:
            raise self._falla
        return SimpleNamespace(content=[SimpleNamespace(text=self._texto)],
                               usage=SimpleNamespace(input_tokens=120, output_tokens=30),
                               stop_reason=self._fin)


def _diag(caso):
    return diagnosticar(verificar_paso(caso["s_i"], caso["s_i_mas_1"]).discrepancia)


@pytest.mark.parametrize("caso", CON_CATEGORIA, ids=[c["id"] for c in CON_CATEGORIA])
def test_envia_parametros_y_datos(caso):
    cliente = ClienteFalso()
    r = llm.generar_retroalimentacion_llm(_diag(caso), caso["s_i"], caso["s_i_mas_1"], cliente=cliente)
    llamada = cliente.llamadas[0]
    assert llamada["model"] == llm.MODELO
    assert llamada["max_tokens"] == llm.MAX_TOKENS
    assert ("temperature" in llamada) == (llm.TEMPERATURA is not None)
    assert caso["s_i"] in llamada["messages"][0]["content"]
    assert caso["s_i_mas_1"] in llamada["messages"][0]["content"]
    assert "{" not in llamada["system"]
    assert r.texto == "Mira el signo de ese término."
    assert r.usado_llm and r.modo == "llm"


def test_registra_latencia_y_tokens():
    caso = CON_CATEGORIA[0]
    r = llm.generar_retroalimentacion_llm(_diag(caso), cliente=ClienteFalso())
    assert r.tokens_entrada == 120 and r.tokens_salida == 30
    assert r.latencia_ms >= 0 and r.modelo == llm.MODELO


def test_no_pasa_la_diferencia_algebraica():
    caso = CON_CATEGORIA[0]
    resultado = _diag(caso)
    cliente = ClienteFalso()
    llm.generar_retroalimentacion_llm(resultado, caso["s_i"], caso["s_i_mas_1"], cliente=cliente)
    assert str(resultado.detalles["diferencia"]) not in cliente.llamadas[0]["messages"][0]["content"]


def test_indeterminado_no_llama_al_llm():
    cliente = ClienteFalso()
    r = llm.generar_retroalimentacion_llm(ResultadoDiagnostico("indeterminado", {}), cliente=cliente)
    assert cliente.llamadas == []
    assert r.texto == MENSAJE_GENERAL and not r.usado_llm


def test_falla_del_servicio_se_convierte_en_llm_no_disponible():
    caso = CON_CATEGORIA[0]
    with pytest.raises(llm.LLMNoDisponible):
        llm.generar_retroalimentacion_llm(_diag(caso), cliente=ClienteFalso(falla=TimeoutError()))


def test_respuesta_vacia_es_error():
    caso = CON_CATEGORIA[0]
    with pytest.raises(llm.LLMNoDisponible):
        llm.generar_retroalimentacion_llm(_diag(caso), cliente=ClienteFalso(texto="  "))


def test_sin_clave_de_api(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    caso = CON_CATEGORIA[0]
    with pytest.raises(llm.LLMNoDisponible):
        llm.generar_retroalimentacion_llm(_diag(caso))


# ---- controles de la respuesta: terminó con normalidad, límite de palabras y formato ----
RESPUESTAS = json.loads((Path(__file__).parent / "datos" / "llm_respuestas.json").read_text(encoding="utf-8"))


def _generar(texto, fin="end_turn"):
    return llm.generar_retroalimentacion_llm(_diag(CON_CATEGORIA[0]), cliente=ClienteFalso(texto, fin=fin))


def test_una_respuesta_cortada_por_el_limite_de_tokens_no_se_entrega():
    with pytest.raises(llm.LLMNoDisponible, match="max_tokens"):
        _generar("Para corregir el error, primero debes dividir ambos lados entre", fin="max_tokens")


@pytest.mark.parametrize("fin", ["end_turn", "stop_sequence"])
def test_una_respuesta_que_termino_con_normalidad_se_entrega(fin):
    assert _generar("Revisa el paso.", fin=fin).motivo_fin == fin


@pytest.mark.parametrize("caso", RESPUESTAS, ids=[c["id"] for c in RESPUESTAS])
def test_el_formato_se_revisa_y_la_pista_no_se_modifica(caso):
    r = _generar(caso["texto"])
    assert list(r.incumplimientos) == caso["esperado"]
    assert r.texto == caso["texto"].strip()


def test_el_limite_de_palabras_se_cumple_en_el_limite_y_se_registra_al_pasarlo():
    en_el_limite = " ".join(["palabra"] * llm.MAX_PALABRAS)
    assert llm.revisar_formato(en_el_limite) == []
    assert llm.revisar_formato(en_el_limite + " palabra") == ["demasiado_larga"]
