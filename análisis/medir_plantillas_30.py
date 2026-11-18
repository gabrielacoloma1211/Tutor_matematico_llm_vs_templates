"""Mide cuánto tarda el generador con plantillas en los 30 pasos de la evaluación con docentes.

No modifica nada: solo lee evaluacion/docentes/pistas_originales.json y llama a las funciones del repositorio.
Uso, desde la carpeta del repositorio:
    python /ruta/a/medir_plantillas_30.py
Mismo método que evaluacion/medir_latencia.py: una pasada de calentamiento que se descarta y 10 repeticiones por
paso, de las que se toma la mediana; se reportan media, mediana, percentil 95 y máximo en milisegundos.
"""
import json
import platform
import statistics as st
import sys
import time

sys.path.insert(0, ".")
import sympy  # noqa: E402
from src.diagnostico.diagnostico import diagnosticar  # noqa: E402
from src.generador.plantillas import generar_retroalimentacion_plantilla as plantilla  # noqa: E402
from src.verificador.verificador import verificar_paso  # noqa: E402

casos = json.load(open("evaluacion/docentes/pistas_originales.json", encoding="utf-8"))["casos"].values()
datos = []
for c in casos:
    d = diagnosticar(verificar_paso(c["paso_anterior"], c["paso_erroneo"]).discrepancia)
    datos.append((d, c["paso_anterior"], c["paso_erroneo"]))
for a in datos:
    plantilla(*a)  # calentamiento (se descarta)
medianas = []
for a in datos:
    t = []
    for _ in range(10):
        ini = time.perf_counter()
        plantilla(*a)
        t.append((time.perf_counter() - ini) * 1000)
    medianas.append(st.median(t))
s = sorted(medianas)
print(f"Python {platform.python_version()} | SymPy {sympy.__version__} | {platform.platform()}")
print(f"plantillas  {len(s)} llamadas | media {st.mean(s):.3f} | mediana {st.median(s):.3f} | "
      f"p95 {s[min(len(s) - 1, int(0.95 * len(s)))]:.3f} | máx {max(s):.3f}  (ms)")
