"""Las métricas por categoría deben contar como fallo un caso en que el diagnóstico lanzó una excepción (ERROR)."""
from collections import Counter

from evaluacion.comun import CATEGORIAS, metricas, resumen


def _confusion_signo(aciertos, errores):
    """Diez casos de error de signo: `aciertos` bien clasificados y `errores` con excepción (ERROR)."""
    return Counter({("error_signo", "error_signo"): aciertos, ("error_signo", "ERROR"): errores})


def test_una_excepcion_cuenta_como_falso_negativo():
    filas, _ = metricas(_confusion_signo(9, 1))
    precision, recall, f1, casos = filas["error_signo"]
    assert recall == 0.9
    assert casos == 10
    assert precision == 1.0


def test_sin_excepciones_el_recall_no_cambia():
    filas, _ = metricas(_confusion_signo(10, 0))
    assert filas["error_signo"][1] == 1.0


def test_las_excepciones_bajan_el_macro_f1():
    _, con_error = metricas(_confusion_signo(9, 1))
    _, sin_error = metricas(_confusion_signo(10, 0))
    assert con_error < sin_error


def test_el_resumen_muestra_la_columna_error_solo_si_hay_excepciones():
    casos = [{"id": f"C{i}", "categoria": "error_signo"} for i in range(10)]
    preds = {c["id"]: "error_signo" for c in casos}
    assert "ERROR" not in resumen(casos, preds, "prueba").splitlines()[1]
    preds["C0"] = "ERROR"
    texto = resumen(casos, preds, "prueba")
    assert "ERROR" in texto.splitlines()[1]
    assert "exactitud 9/10" in texto
    assert len(CATEGORIAS) == 6
