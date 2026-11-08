"""Cada experimento con el LLM debe guardar con qué configuración se hizo (modelo, parámetros, prompt, commit)."""
import subprocess

from evaluacion import comun
from src.generador import llm


def test_la_configuracion_registra_modelo_parametros_y_version_del_prompt():
    c = comun.configuracion_experimento()
    assert c["modelo"] == llm.MODELO
    assert c["temperatura"] == llm.TEMPERATURA
    assert c["max_tokens"] == llm.MAX_TOKENS
    assert c["timeout_segundos"] == llm.TIMEOUT_SEGUNDOS
    assert len(c["fecha"]) == 10
    assert list(c["prompts"]) == [llm.RUTA_PROMPT.name]
    assert all(len(h) == 16 for h in c["prompts"].values())


def test_cambiar_el_texto_del_prompt_cambia_su_huella(tmp_path):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("uno", encoding="utf-8")
    b.write_text("dos", encoding="utf-8")
    ha = comun.configuracion_experimento([a])["prompts"]["a.txt"]
    hb = comun.configuracion_experimento([b])["prompts"]["b.txt"]
    assert ha != hb


def test_sin_git_el_commit_queda_en_none(monkeypatch):
    def sin_git(*a, **k):
        raise FileNotFoundError("git")
    monkeypatch.setattr(subprocess, "run", sin_git)
    c = comun.configuracion_experimento()
    assert c["commit"] is None and c["cambios_sin_guardar"] is None
