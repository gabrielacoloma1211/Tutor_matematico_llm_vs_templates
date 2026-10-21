"""
Pruebas de la validación de seguridad de las ecuaciones (src/verificador/entrada.py).

Ninguna entrada llega a `parse_expr` de SymPy sin pasar por esta validación. Se prueba que
admita las ecuaciones del proyecto y que rechace las mal escritas, las que usan algo no
autorizado (código, funciones, otras variables u operadores) y las demasiado grandes o
complejas. Los ejemplos están en tests/datos/entradas.json.
"""
import pytest

from src.verificador.entrada import EntradaNoPermitida, validar_ecuacion
from src.verificador.verificador import ErrorDeParseo, parsear_ecuacion, verificar_paso
from tests.datos import cargar

DATOS = cargar("entradas")


def _ids(lista):
    return [e["id"] for e in lista]


@pytest.mark.parametrize("e", DATOS["admitidas"], ids=_ids(DATOS["admitidas"]))
def test_las_ecuaciones_del_proyecto_se_admiten(e):
    validar_ecuacion(e["ecuacion"])
    izq, der = parsear_ecuacion(e["ecuacion"])
    assert izq is not None and der is not None


@pytest.mark.parametrize("e", DATOS["mal_escritas"], ids=_ids(DATOS["mal_escritas"]))
def test_una_ecuacion_mal_escrita_es_un_error_de_formato(e):
    with pytest.raises(EntradaNoPermitida) as info:
        validar_ecuacion(e["ecuacion"])
    assert info.value.tipo == "error_de_formato"
    with pytest.raises(ErrorDeParseo) as info:
        parsear_ecuacion(e["ecuacion"])
    assert info.value.tipo == "error_de_formato"


@pytest.mark.parametrize("e", DATOS["no_permitidas"], ids=_ids(DATOS["no_permitidas"]))
def test_lo_no_autorizado_se_rechaza_antes_de_llegar_a_sympy(e):
    with pytest.raises(EntradaNoPermitida) as info:
        validar_ecuacion(e["ecuacion"])
    assert info.value.tipo == "entrada_no_permitida"
    with pytest.raises(ErrorDeParseo) as info:
        parsear_ecuacion(e["ecuacion"])
    assert info.value.tipo == "entrada_no_permitida"


@pytest.mark.parametrize("e", DATOS["demasiado_complejas"], ids=_ids(DATOS["demasiado_complejas"]))
def test_lo_demasiado_largo_o_complejo_se_rechaza(e):
    with pytest.raises(ErrorDeParseo) as info:
        parsear_ecuacion(e["ecuacion"])
    assert info.value.tipo == "entrada_no_permitida"


@pytest.mark.parametrize("e", DATOS["division_entre_cero"], ids=_ids(DATOS["division_entre_cero"]))
def test_una_division_entre_cero_se_rechaza(e):
    with pytest.raises(ErrorDeParseo):
        parsear_ecuacion(e["ecuacion"])


def test_una_entrada_no_autorizada_no_ejecuta_codigo(monkeypatch):
    """Si algo llegara a parse_expr, esta prueba fallaría: se reemplaza por una función que avisa."""
    import src.verificador.verificador as v

    def _no_debe_llamarse(*a, **k):
        raise AssertionError("parse_expr no debe recibir entradas no validadas")

    monkeypatch.setattr(v, "parse_expr", _no_debe_llamarse)
    for e in DATOS["no_permitidas"] + DATOS["mal_escritas"] + DATOS["demasiado_complejas"]:
        with pytest.raises(ErrorDeParseo):
            verificar_paso(e["ecuacion"], e["ecuacion"])


def test_una_entrada_que_no_es_texto_se_rechaza():
    for malo in (None, 5, [], b"", 2.5):
        with pytest.raises(EntradaNoPermitida):
            validar_ecuacion(malo)
