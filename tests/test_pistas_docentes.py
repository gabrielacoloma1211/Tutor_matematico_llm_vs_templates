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


# --- Protección del cegamiento: los archivos que revelan el origen de las pistas no deben llegar a Git ---

RAIZ = Path(g.RAIZ)


def test_gitignore_excluye_los_archivos_que_rompen_el_cegamiento():
    from fnmatch import fnmatch
    reglas = [linea.strip() for linea in (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
              if linea.strip() and not linea.startswith("#")]
    for nombre in g.ARCHIVOS_PRIVADOS:
        ruta = f"evaluacion/docentes/{nombre}"
        assert any(fnmatch(ruta, r.lstrip("/")) or fnmatch(nombre, r) for r in reglas), nombre
    assert "PLANTILLA_DOCENTES.md" not in reglas  # la hoja vacía sí es parte del repositorio


def test_la_hoja_para_los_docentes_no_contiene_la_clave(carpeta):
    g.main(["--carpeta", str(carpeta)], cliente=ClienteFalso())
    hoja = (carpeta / "HOJAS_DOCENTES_con_pistas.md").read_text(encoding="utf-8")
    clave = _leer(carpeta, "CLAVE_AB_no_entregar.json")
    assert "CLAVE" not in hoja and "asignacion" not in hoja and clave["semilla"] is not None
    for nombre in ("llm", "plantilla"):
        assert nombre not in hoja.lower().replace("plantilla_docentes", "")


def _repo_git(carpeta, gitignore):
    import subprocess
    subprocess.run(["git", "init", "-q", str(carpeta)], check=True)
    if gitignore is not None:
        (carpeta / ".gitignore").write_text(gitignore, encoding="utf-8")


def test_el_script_se_detiene_si_los_archivos_privados_no_estan_en_gitignore(carpeta):
    _repo_git(carpeta, gitignore="")
    with pytest.raises(SystemExit) as e:
        g.main(["--carpeta", str(carpeta)], cliente=ClienteFalso())
    assert "CLAVE_AB_no_entregar.json" in str(e.value)
    assert not (carpeta / "CLAVE_AB_no_entregar.json").exists()


def test_el_script_sigue_si_los_archivos_privados_estan_en_gitignore(carpeta):
    _repo_git(carpeta, gitignore="\n".join(g.ARCHIVOS_PRIVADOS) + "\n")
    g.main(["--carpeta", str(carpeta)], cliente=ClienteFalso())
    assert (carpeta / "CLAVE_AB_no_entregar.json").exists()


# --- Una ejecución reanudada debe tener la misma configuración que la que empezó ---

def _primera_ejecucion_incompleta(carpeta):
    """Genera todo salvo la pista del LLM de un caso (la llamada número 10 falla), como si se hubiera cortado."""
    assert g.main(["--carpeta", str(carpeta)], cliente=ClienteFalso(fallan={10})) == 1
    return _leer(carpeta, "pistas_originales.json")


def _modelo_nuevo(monkeypatch):
    monkeypatch.setattr(llm, "MODELO", "otro-modelo-distinto")


def _prompt_nuevo(monkeypatch, tmp_path):
    nuevo = tmp_path / "prompt_llm.txt"
    nuevo.write_text(llm.RUTA_PROMPT.read_text(encoding="utf-8") + "\nUna frase más.", encoding="utf-8")
    monkeypatch.setattr(llm, "RUTA_PROMPT", nuevo)


def _tokens_nuevos(monkeypatch):
    monkeypatch.setattr(llm, "MAX_TOKENS", llm.MAX_TOKENS + 1)


def _temperatura_nueva(monkeypatch):
    monkeypatch.setattr(llm, "TEMPERATURA", 0.2)


def _commit_nuevo(monkeypatch, tmp_path):
    from evaluacion import comun
    monkeypatch.setattr(comun, "_commit_actual", lambda: {"commit": "otro-commit", "cambios_sin_guardar": False})


@pytest.mark.parametrize("cambio, mencion", [
    ("modelo", "modelo"), ("prompt", "prompt_llm.txt"), ("tokens", "max_tokens"),
    ("temperatura", "temperatura"), ("commit", "commit"),
])
def test_no_se_reanuda_si_cambio_la_configuracion(carpeta, tmp_path, monkeypatch, cambio, mencion):
    antes = _primera_ejecucion_incompleta(carpeta)
    {"modelo": lambda: _modelo_nuevo(monkeypatch), "prompt": lambda: _prompt_nuevo(monkeypatch, tmp_path),
     "tokens": lambda: _tokens_nuevos(monkeypatch), "temperatura": lambda: _temperatura_nueva(monkeypatch),
     "commit": lambda: _commit_nuevo(monkeypatch, tmp_path)}[cambio]()
    cliente = ClienteFalso()
    with pytest.raises(SystemExit) as e:
        g.main(["--carpeta", str(carpeta), "--reintentar"], cliente=cliente)
    assert mencion in str(e.value) and "no se reanuda" in str(e.value)
    assert cliente.llamadas == 0                                             # no se llamó al LLM
    assert _leer(carpeta, "pistas_originales.json") == antes                 # no se tocó nada
    assert not (carpeta / "CLAVE_AB_no_entregar.json").exists()
    assert not (carpeta / "HOJAS_DOCENTES_con_pistas.md").exists()


def test_se_reanuda_si_la_configuracion_es_la_misma_aunque_cambie_la_fecha(carpeta, monkeypatch):
    _primera_ejecucion_incompleta(carpeta)
    ruta = carpeta / "pistas_originales.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    datos["configuracion"]["fecha"] = "2020-01-01"          # otra fecha: no cuenta como cambio
    ruta.write_text(json.dumps(datos), encoding="utf-8")
    cliente = ClienteFalso()
    assert g.main(["--carpeta", str(carpeta), "--reintentar"], cliente=cliente) == 0
    assert cliente.llamadas == 1


def test_diferencias_de_configuracion_vacia_si_son_iguales():
    c = {"fecha": "2026-11-09", "modelo": "m", "prompts": {"a.txt": "1"}, "commit": "x"}
    assert g.diferencias_de_configuracion(c, {**c, "fecha": "2026-11-10"}) == []
    assert g.diferencias_de_configuracion(c, {**c, "prompts": {"a.txt": "2"}}) == ["prompt a.txt: 1 -> 2"]
