"""
Mide la latencia del verificador y del diagnóstico (componentes deterministas).

Método:
  - Datos: los casos de dev (no se usa test: está reservado).
  - Verificador: todas las transiciones de la resolución del estudiante.
  - Diagnóstico: solo los pasos erróneos (es cuando se ejecuta).
  - Calentamiento: una pasada completa que se descarta (cachés de SymPy, imports).
  - Cada llamada se repite N veces; el tiempo de esa llamada es la mediana de las N.
  - Se reportan media, mediana, percentil 95 y máximo sobre las llamadas, en ms.
Mide solo las funciones de Python: no incluye el servidor ni la red.

Uso (desde la raíz del repositorio):
    python evaluacion/medir_latencia.py
    python evaluacion/medir_latencia.py --repeticiones 10 --guardar
"""
import argparse
import glob
import json
import platform
import statistics as st
import sys
import time
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import sympy  # noqa: E402
from src.diagnostico.diagnostico import diagnosticar  # noqa: E402
from src.verificador.verificador import verificar_paso  # noqa: E402


def _ms(f, *args):
    t = time.perf_counter()
    r = f(*args)
    return (time.perf_counter() - t) * 1000, r


def _mediana_de_repeticiones(f, args, n):
    return st.median(_ms(f, *args)[0] for _ in range(n))


def _fila(nombre, tiempos):
    t = sorted(tiempos)
    p95 = t[min(len(t) - 1, int(0.95 * len(t)))]
    return (f"{nombre:<13}{len(t):>6} llamadas | media {st.mean(t):6.1f} | mediana {st.median(t):6.1f} | "
            f"p95 {p95:6.1f} | máx {max(t):6.1f}  (ms)")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeticiones", type=int, default=5)
    ap.add_argument("--guardar", action="store_true")
    a = ap.parse_args(argv)

    casos = [c for f in sorted(glob.glob(str(RAIZ / "benchmark" / "casos" / "dev" / "*.json")))
             for c in json.load(open(f, encoding="utf-8"))]
    transiciones, erroneos = [], []
    for c in casos:
        est = c["resolucion_estudiante"]
        for i in range(1, len(est)):
            transiciones.append((est[i - 1], est[i]))
            if i == c["indice_paso_erroneo"]:
                erroneos.append((est[i - 1], est[i]))

    for p in transiciones:  # calentamiento (se descarta)
        verificar_paso(*p)
    for p in erroneos:
        diagnosticar(verificar_paso(*p).discrepancia)

    tv = [_mediana_de_repeticiones(verificar_paso, p, a.repeticiones) for p in transiciones]
    td = []
    for p in erroneos:
        disc = verificar_paso(*p).discrepancia
        td.append(_mediana_de_repeticiones(diagnosticar, (disc,), a.repeticiones))

    cab = (f"Latencia sobre dev ({len(casos)} casos), {a.repeticiones} repeticiones por llamada (se usa la mediana), "
           f"1 pasada de calentamiento descartada.\n"
           f"Python {platform.python_version()} | SymPy {sympy.__version__} | {platform.platform()} | {platform.processor() or platform.machine()}")
    out = "\n".join([cab, _fila("verificador", tv), _fila("diagnóstico", td),
                     f"suma de medias (un paso inválido): {st.mean(tv) + st.mean(td):.1f} ms"])
    print(out)
    if a.guardar:
        dest = RAIZ / "evaluacion" / "resultados" / f"latencia_{date.today().isoformat()}.txt"
        dest.write_text(out + "\n", encoding="utf-8")
        print("guardado en", dest.relative_to(RAIZ))


if __name__ == "__main__":
    main()
