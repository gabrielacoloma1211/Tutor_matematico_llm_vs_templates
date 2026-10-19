"""
Evalúa el módulo de diagnóstico sobre el conjunto AMPLIADO (100 casos
generados por un LLM y etiquetados por la autora). Es un conjunto aparte del
benchmark: no se mezcla con dev ni test.

Cada caso tiene `categoria` (la que asignó la autora) y `tipo_de_novedad`
(variante_nueva, estructura_nueva, combinado, fuera_de_taxonomia).
`benchmark/casos/ampliado/particion.json` separa los casos de ajuste de los
reservados (estos últimos no se usan para modificar reglas).

Uso (desde la raíz del repositorio):
    python evaluacion/evaluar_ampliado.py
    python evaluacion/evaluar_ampliado.py --guardar   # guarda el resultado con fecha
"""
import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from evaluacion.evaluar_diagnostico import CATEGORIAS, CORTO, metricas, predecir  # noqa: E402

DIR = RAIZ / "benchmark" / "casos" / "ampliado"


def resumen(casos, preds, titulo):
    confusion = Counter((c["categoria"], preds[c["id"]]) for c in casos)
    filas, macro = metricas(confusion)
    ok = sum(confusion[(k, k)] for k in CATEGORIAS)
    out = [f"== {titulo}: {len(casos)} casos | exactitud {ok}/{len(casos)} = {ok/len(casos):.2f} | macro-F1 {macro:.2f}"]
    out.append(f"{'':<9}" + "".join(f"{CORTO[c]:>8}" for c in CATEGORIAS))
    for real in CATEGORIAS:
        out.append(f"{CORTO[real]:<9}" + "".join(f"{confusion[(real, p)]:>8}" for p in CATEGORIAS))
    out.append(f"{'categoría':<10}{'casos':>6}{'prec':>7}{'recall':>8}{'F1':>6}")
    for cat in CATEGORIAS:
        p, r, f, n = filas[cat]
        out.append(f"{CORTO[cat]:<10}{n:>6}{p:>7.2f}{r:>8.2f}{f:>6.2f}")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true")
    ap.add_argument("--etiqueta", default="", help="se agrega al nombre del archivo guardado (p. ej. ajustado)")
    args = ap.parse_args(argv)

    casos = json.load(open(DIR / "ampliado.json", encoding="utf-8"))
    part = json.load(open(DIR / "particion.json", encoding="utf-8"))
    preds = {}
    for c in casos:
        try:
            preds[c["id"]] = predecir(c)
        except Exception as e:  # el diagnóstico falló: se registra como ERROR, no se oculta
            preds[c["id"]] = "ERROR"
            print(f"AVISO: {c['id']} produjo {type(e).__name__}")

    partes = [resumen(casos, preds, "TODOS")]
    for nombre, ids in (("AJUSTE", part["ajuste"]), ("RESERVADOS", part["reservados_30"])):
        partes.append(resumen([c for c in casos if c["id"] in set(ids)], preds, nombre))

    # fallos por tipo de novedad: seguros (dice indeterminado) o peligrosos (otra categoría)
    tabla = [f"{'tipo de novedad':<20}{'casos':>6}{'aciertos':>10}{'seguros':>9}{'peligrosos':>12}"]
    for tipo in ("variante_nueva", "estructura_nueva", "combinado", "fuera_de_taxonomia"):
        cs = [c for c in casos if c["tipo_de_novedad"] == tipo]
        ac = sum(preds[c["id"]] == c["categoria"] for c in cs)
        seg = sum(preds[c["id"]] != c["categoria"] and preds[c["id"]] in ("indeterminado", "ERROR") for c in cs)
        tabla.append(f"{tipo:<20}{len(cs):>6}{ac:>10}{seg:>9}{len(cs)-ac-seg:>12}")
    partes.append("== Por tipo de novedad (seguro = responde indeterminado o falla sin clasificar; peligroso = otra categoría)\n" + "\n".join(tabla))

    fallos = [f"  {c['id']:<8} tipo {c['tipo_de_novedad']:<18} autora: {CORTO[c['categoria']]:<8} diagnóstico: {CORTO.get(preds[c['id']], "ERROR")}"
              for c in casos if preds[c["id"]] != c["categoria"]]
    partes.append(f"== Casos mal clasificados ({len(fallos)})\n" + "\n".join(fallos))
    texto = "\n\n".join(partes)
    print(texto)
    if args.guardar:
        d = RAIZ / "evaluacion" / "resultados"
        d.mkdir(exist_ok=True)
        (d / f"ampliado_{date.today().isoformat()}{args.etiqueta}.txt").write_text(texto + "\n", encoding="utf-8")
        (d / f"ampliado_{date.today().isoformat()}{args.etiqueta}_predicciones.json").write_text(
            json.dumps(preds, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
