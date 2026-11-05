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
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from evaluacion.comun import (  # noqa: E402
    guardar_resultado, lista_de_fallos, predecir_todos, resumen, tabla_por_novedad,
)

DIR = RAIZ / "benchmark" / "casos" / "ampliado"
CONJUNTOS = {"ampliado": ("ampliado", "ampliado.json"), "ampliado_2": ("ampliado_2", "ampliado_2.json")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", action="store_true")
    ap.add_argument("--conjunto", choices=sorted(CONJUNTOS), default="ampliado",
                    help="ampliado (el primero) o ampliado_2 (la primera prueba ciega, ya usada para ajustar)")
    ap.add_argument("--etiqueta", default="", help="se agrega al nombre del archivo guardado (p. ej. ajustado)")
    args = ap.parse_args(argv)

    carpeta, archivo = CONJUNTOS[args.conjunto]
    dir_ = RAIZ / "benchmark" / "casos" / carpeta
    casos = json.load(open(dir_ / archivo, encoding="utf-8"))
    part = json.load(open(dir_ / "particion.json", encoding="utf-8"))
    preds = predecir_todos(casos)

    partes = [resumen(casos, preds, "TODOS")]
    for nombre, ids in (("AJUSTE", part["ajuste"]), ("RESERVADOS", (part.get("reservados_30") or part["reservados"]))):
        partes.append(resumen([c for c in casos if c["id"] in set(ids)], preds, nombre))

    # fallos por tipo de novedad: seguros (dice indeterminado) o peligrosos (otra categoría)
    partes.append(tabla_por_novedad(casos, preds))
    partes.append(lista_de_fallos(casos, preds))
    texto = "\n\n".join(partes)
    print(texto)
    if args.guardar:
        guardar_resultado(args.conjunto, f"{args.conjunto}_{date.today().isoformat()}{args.etiqueta}", texto, preds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
