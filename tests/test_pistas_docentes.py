"""Generación de las pistas para los docentes: pareada, ciega, con originales intactos y clave aparte."""
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from evaluacion import generar_pistas_docentes as g
from src.generador import llm

HOJA = Path(g.CARPETA) / "PLANTILLA_DOCENTES.md"


class ClienteFalso:
    """Devuelve una pista distinta en cada llamada; `fallan` = números de llamada que lanzan error."""
    def __init__(self, fallan=()):
        self.llamadas, self._fallan = 0, set(fallan)
        self.messages = self

    def create(self, **kwargs):
        self.llamadas += 1
        if self.llamadas in self._fallan:
            raise RuntimeError("sin servicio")
        return SimpleNamespace(content=[SimpleNamespace(text=f"Pista del modelo número {self.llamadas}.")],
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5), stop_reason="end_turn")


@pytest.fixture
def carpeta(tmp_path):
    shutil.copy(HOJA, tmp_path / "PLANTILLA_DOCENTES.md")
    return tmp_path


def _leer(carpeta, nombre):
    return json.loads((carpeta / nombre).read_text(encoding="utf-8"))


def test_los_30_casos_de_la_hoja_coinciden_con_la_seleccion():
    seleccion = json.loads(g.SELECCION.read_text(encoding="utf-8"))
    casos = g.leer_casos_de_la_hoja(HOJA.read_text(encoding="utf-8"), seleccion)
    assert [n for n, _ in casos] == list(range(1, 31))
    assert len({c["id"] for _, c in casos}) == 30


def test_la_asignacion_ab_esta_balanceada_y_es_reproducible():
    ids = [f"C{i}" for i in range(30)]
    clave = g.asignar_ab(ids)
    assert sum(v["A"] == "llm" for v in clave.values()) == 15
    assert all({v["A"], v["B"]} == {"llm", "plantilla"} for v in clave.values())
    assert clave == g.asignar_ab(ids)


def test_el_flujo_completo_deja_originales_clave_y_hoja(carpeta):
    cliente = ClienteFalso()
    assert g.main(["--carpeta", str(carpeta)], cliente=cliente) == 0
    originales, clave = _leer(carpeta, "pistas_originales.json"), _leer(carpeta, "CLAVE_AB_no_entregar.json")
    assert len(originales["casos"]) == 30 and cliente.llamadas == 30
    assert originales["configuracion"]["modelo"] == llm.MODELO
    hoja = (carpeta / "HOJAS_DOCENTES_con_pistas.md").read_text(encoding="utf-8")
    assert "pegar la pista" not in hoja and "pegar" not in hoja.lower()
    assert "llm" not in hoja.lower() and "CLAVE" not in hoja
    for cid, reg in originales["casos"].items():
        assert reg["llm"]["texto"] in hoja
        assert reg["plantilla"]["texto"] in hoja
        assert {clave["asignacion"][cid]["A"], clave["asignacion"][cid]["B"]} == {"llm", "plantilla"}


def test_la_pista_A_de_la_hoja_es_la_que_dice_la_clave(carpeta):
    g.main(["--carpeta", str(carpeta)], cliente=ClienteFalso())
    originales, clave = _leer(carpeta, "pistas_originales.json"), _leer(carpeta, "CLAVE_AB_no_entregar.json")
    hoja = (carpeta / "HOJAS_DOCENTES_con_pistas.md").read_text(encoding="utf-8")
    for cid, reg in originales["casos"].items():
        mecanismo_a = clave["asignacion"][cid]["A"]
        assert f"**Pista A:** {g._escapar(reg[mecanismo_a]['texto'])}" in hoja


def test_una_segunda_corrida_no_regenera_ni_cambia_nada(carpeta):
    g.main(["--carpeta", str(carpeta)], cliente=ClienteFalso())
    antes = {n: (carpeta / n).read_text(encoding="utf-8")
             for n in ("pistas_originales.json", "CLAVE_AB_no_entregar.json", "HOJAS_DOCENTES_con_pistas.md")}
    otro = ClienteFalso()
    assert g.main(["--carpeta", str(carpeta)], cliente=otro) == 0
    assert otro.llamadas == 0
    for n, texto in antes.items():
        assert (carpeta / n).read_text(encoding="utf-8") == texto


def test_si_el_llm_falla_no_se_crea_clave_ni_hoja_y_se_puede_reintentar(carpeta):
    assert g.main(["--carpeta", str(carpeta)], cliente=ClienteFalso(fallan={3})) == 1
    assert not (carpeta / "CLAVE_AB_no_entregar.json").exists()
    assert not (carpeta / "HOJAS_DOCENTES_con_pistas.md").exists()
    antes = _leer(carpeta, "pistas_originales.json")
    exitosas = {c: r["llm"]["texto"] for c, r in antes["casos"].items() if "texto" in r["llm"]}
    assert len(exitosas) == 29
    reintento = ClienteFalso()
    assert g.main(["--carpeta", str(carpeta), "--reintentar"], cliente=reintento) == 0
    assert reintento.llamadas == 1
    despues = _leer(carpeta, "pistas_originales.json")
    assert all(despues["casos"][c]["llm"]["texto"] == t for c, t in exitosas.items())


def test_solo_comprobar_no_llama_al_llm_ni_escribe_archivos(carpeta):
    cliente = ClienteFalso()
    assert g.main(["--carpeta", str(carpeta), "--solo-comprobar"], cliente=cliente) == 0
    assert cliente.llamadas == 0
    assert [p.name for p in carpeta.iterdir()] == ["PLANTILLA_DOCENTES.md"]
