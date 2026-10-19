"""
Evalúa el diagnóstico (congelado tras el ajuste) sobre las 50 variaciones de AMP-010 y AMP-071
(otros números, mismo tipo de error). Las etiquetas fueron revisadas por la autora.

Uso:  python evaluacion/evaluar_variaciones.py [archivo.json] [_etiqueta] [--guardar]
"""
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from evaluacion.evaluar_diagnostico import predecir  # noqa: E402

ARCHIVO = next((a for a in sys.argv[1:] if a.endswith(".json")), "variaciones.json")
ETQ = next((a for a in sys.argv[1:] if a.startswith("_")), "")
casos = json.load(open(RAIZ / "benchmark/casos/variaciones" / ARCHIVO, encoding="utf-8"))
preds = {}
for c in casos:
    try:
        preds[c["id"]] = predecir(c)
    except Exception as e:
        preds[c["id"]] = "ERROR"
out = []
for sem in ("AMP-010", "AMP-071"):
    sub = [c for c in casos if c["caso_semilla"] == sem]
    cnt = Counter(preds[c["id"]] for c in sub)
    ok = cnt["indeterminado"]
    out.append(f"{sem}: {len(sub)} variaciones | etiqueta esperada: indeterminado | acierta {ok}/{len(sub)}")
    out.append("   respuestas del diagnóstico: " + ", ".join(f"{k}={v}" for k, v in cnt.most_common()))
tot = sum(preds[c["id"]] == c["categoria"] for c in casos)
out.append(f"TOTAL: {tot}/{len(casos)}")
out.append("Fallos:")
for c in casos:
    if preds[c["id"]] != c["categoria"]:
        out.append(f"  {c['id']} {c['resolucion_estudiante'][0]} -> {c['resolucion_estudiante'][1]}  diag={preds[c['id']]}")
txt = "\n".join(out)
print(txt)
if "--guardar" in sys.argv:
    d = RAIZ / "evaluacion/resultados"
    (d / f"{ARCHIVO[:-5]}_{date.today().isoformat()}{ETQ}.txt").write_text(txt + "\n", encoding="utf-8")
    json.dump(preds, open(d / f"{ARCHIVO[:-5]}_{date.today().isoformat()}{ETQ}_predicciones.json", "w"), indent=1)
