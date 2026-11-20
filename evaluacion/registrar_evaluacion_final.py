"""
Deja por escrito la evaluación final del diagnóstico sobre el conjunto TEST (50 casos).

NO cambia ninguna regla ni ajusta nada: corre el diagnóstico congelado (etiqueta `v1.0-congelado`) sobre los
casos test y guarda los identificadores, la etiqueta de referencia de la autora, la predicción, la matriz de
confusión, las métricas, el commit y las huellas del código y de los casos. Es un registro de la evaluación ya
realizada (11 de noviembre de 2026); el resultado se contrasta con lo que reporta la memoria (49/50, macro-F1 0,98).

Uso (desde la raíz del repositorio):
    python evaluacion/registrar_evaluacion_final.py --evaluacion-final --guardar
"""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from benchmark.validar_casos import cargar_casos  # noqa: E402
from evaluacion.comun import CATEGORIAS, CORTO, metricas, predecir_todos, resumen  # noqa: E402

ETIQUETA = "v1.0-congelado"
DESTINO = RAIZ / "evaluacion" / "resultados" / "evaluacion_final"


def _git(*args):
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()


def _huella(rutas):
    h = hashlib.sha256()
    for r in sorted(rutas):
        h.update(r.relative_to(RAIZ).as_posix().encode())
        h.update(r.read_bytes())
    return h.hexdigest()[:16]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--evaluacion-final", action="store_true", help="confirma que es un registro, sin ajustes")
    ap.add_argument("--guardar", action="store_true")
    args = ap.parse_args(argv)
    if not args.evaluacion_final:
        print("El conjunto TEST solo se usa para documentar la evaluación final. Agrega --evaluacion-final.")
        return 2

    casos = [c for _, c in cargar_casos(RAIZ / "benchmark" / "casos" / "test")]
    casos.sort(key=lambda c: c["id"])
    preds = predecir_todos(casos)

    commit_etiqueta = _git("rev-list", "-n1", ETIQUETA)
    codigo = [r for d in ("verificador", "diagnostico") for r in (RAIZ / "src" / d).glob("*.py")]
    codigo.append(RAIZ / "data" / "taxonomia.json")
    cambios = _git("diff", "--name-only", ETIQUETA, "--", "src/verificador", "src/diagnostico", "data/taxonomia.json",
                   "benchmark/casos/test")
    confusion = Counter((c["categoria"], preds[c["id"]]) for c in casos)
    filas, macro = metricas(confusion)
    aciertos = sum(confusion[(k, k)] for k in CATEGORIAS)
    fallos = [{"id": c["id"], "referencia": c["categoria"], "prediccion": preds[c["id"]]}
              for c in casos if preds[c["id"]] != c["categoria"]]

    registro = {
        "descripcion": "Registro de la evaluación final del diagnóstico sobre el conjunto TEST (medido una sola vez, sin ajustes).",
        "conjunto": "test", "n_casos": len(casos),
        "fecha_evaluacion_original": "2026-11-11",
        "fecha_de_este_registro": date.today().isoformat(),
        "etiqueta_codigo_congelado": ETIQUETA,
        "commit_codigo_congelado": commit_etiqueta,
        "commit_al_generar_registro": _git("rev-parse", "HEAD"),
        "codigo_evaluado_identico_a_la_etiqueta": cambios == "",
        "huella_codigo": _huella(codigo),
        "huella_casos_test": _huella(sorted((RAIZ / "benchmark" / "casos" / "test").glob("*.json"))),
        "aciertos": aciertos, "exactitud": round(aciertos / len(casos), 4), "macro_f1": round(macro, 4),
        "metricas_por_categoria": {c: {"casos": filas[c][3], "precision": round(filas[c][0], 4),
                                        "recall": round(filas[c][1], 4), "f1": round(filas[c][2], 4)}
                                   for c in CATEGORIAS},
        "matriz_confusion": {real: {p: confusion[(real, p)] for p in CATEGORIAS} for real in CATEGORIAS},
        "fallos": fallos,
        "casos": [{"id": c["id"], "referencia": c["categoria"], "prediccion": preds[c["id"]],
                   "acierto": preds[c["id"]] == c["categoria"]} for c in casos],
    }
    texto = [resumen(casos, preds, "EVALUACIÓN FINAL (TEST)"),
             f"\nCasos mal clasificados ({len(fallos)}): " + (", ".join(
                 f"{f['id']} (referencia {CORTO[f['referencia']]}, diagnóstico {CORTO[f['prediccion']]})" for f in fallos) or "ninguno"),
             f"\ncommit del código congelado ({ETIQUETA}): {commit_etiqueta}",
             f"código idéntico a la etiqueta: {registro['codigo_evaluado_identico_a_la_etiqueta']}",
             f"huella del código: {registro['huella_codigo']} | huella de los casos test: {registro['huella_casos_test']}"]
    print("\n".join(texto))

    if args.guardar:
        DESTINO.mkdir(parents=True, exist_ok=True)
        base = "evaluacion_final_test"
        (DESTINO / f"{base}.txt").write_text("\n".join(texto) + "\n", encoding="utf-8")
        (DESTINO / f"{base}_registro.json").write_text(json.dumps(registro, indent=2, ensure_ascii=False) + "\n",
                                                       encoding="utf-8")
        with open(DESTINO / f"{base}_predicciones.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "referencia", "prediccion", "acierto"])
            for c in registro["casos"]:
                w.writerow([c["id"], c["referencia"], c["prediccion"], int(c["acierto"])])
        print(f"\nGuardado en {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
