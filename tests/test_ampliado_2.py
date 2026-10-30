"""
Pruebas del conjunto ampliado 2: los 100 casos de la primera prueba ciega, que dejaron de ser ciegos
cuando se ajustaron reglas con ellos. Se dividen en casos de ajuste (se usaron para decidir cambios) y
casos reservados (no se usaron). Los casos están en benchmark/casos/ampliado_2.
"""
import json
from pathlib import Path

import pytest

from benchmark.validar_casos import CATEGORIAS, RAIZ, validar_caso
from evaluacion.evaluar_diagnostico import predecir

DIR = Path(RAIZ) / "benchmark" / "casos" / "ampliado_2"
CASOS = json.loads((DIR / "ampliado_2.json").read_text(encoding="utf-8"))
PARTICION = json.loads((DIR / "particion.json").read_text(encoding="utf-8"))
TIPOS = {"variante_nueva", "estructura_nueva", "combinado", "fuera_de_taxonomia"}
AJUSTE = [c for c in CASOS if c["id"] in set(PARTICION["ajuste"])]


def test_hay_100_casos_con_ids_unicos_y_la_particion_es_completa():
    ids = [c["id"] for c in CASOS]
    assert len(ids) == 100 and len(set(ids)) == 100
    assert set(PARTICION["ajuste"]) | set(PARTICION["reservados"]) == set(ids)
    assert not set(PARTICION["ajuste"]) & set(PARTICION["reservados"])


def test_los_reservados_tienen_casos_de_todas_las_categorias():
    reservados = {c["categoria"] for c in CASOS if c["id"] in set(PARTICION["reservados"])}
    assert reservados == set(CATEGORIAS)


@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_cada_caso_es_consistente(caso):
    assert validar_caso(caso) == []
    assert caso["categoria"] in CATEGORIAS
    assert caso["tipo_de_novedad"] in TIPOS


@pytest.mark.parametrize("caso", AJUSTE, ids=[c["id"] for c in AJUSTE])
def test_los_casos_de_ajuste_se_diagnostican_como_etiqueto_la_autora(caso):
    if caso["id"] in PARTICION["sin_resolver_a_proposito"]:
        pytest.skip(PARTICION["sin_resolver_a_proposito"][caso["id"]])
    assert predecir(caso) == caso["categoria"]


def test_los_casos_sin_resolver_estan_justificados_y_siguen_fallando():
    for id_ in PARTICION["sin_resolver_a_proposito"]:
        caso = next(c for c in CASOS if c["id"] == id_)
        assert predecir(caso) != caso["categoria"], f"{id_} ya se resuelve: se quita de la lista"
