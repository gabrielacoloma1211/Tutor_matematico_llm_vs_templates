"""
Evalúa el módulo de diagnóstico sobre los casos del benchmark.

Para cada caso toma el paso erróneo del estudiante (de la resolución del
estudiante, el paso de índice `indice_paso_erroneo` con el paso anterior),
lo pasa por el verificador y el diagnóstico, y compara la categoría que
asigna el diagnóstico con la que escribió la autora.

Muestra la matriz de confusión, y la precisión, el recall y el F1 de cada
categoría, junto con el macro-F1.

Por defecto usa el conjunto DEV, con el que se diseñan y ajustan las reglas.
El conjunto TEST está reservado para la evaluación final y no debe usarse
para decidir cambios en las reglas; por eso exige --evaluacion-final.

Uso (desde la raíz del repositorio):
    python evaluacion/evaluar_diagnostico.py
    python evaluacion/evaluar_diagnostico.py --conjunto test --evaluacion-final
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from benchmark.validar_casos import cargar_casos  # noqa: E402
from evaluacion.comun import (  # noqa: E402,F401  (algunos nombres los importan otros scripts y las pruebas)
    CATEGORIAS, CORTO, macro_f1_presentes, metricas, predecir, texto_macro_presentes,
)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Evalúa el módulo de diagnóstico sobre el benchmark.")
    ap.add_argument("--conjunto", choices=["dev", "test"], default="dev")
    ap.add_argument("--evaluacion-final", action="store_true",
                    help="necesario para usar el conjunto test (reservado para la evaluación final)")
    args = ap.parse_args(argv)

    if args.conjunto == "test" and not args.evaluacion_final:
        print("El conjunto TEST está reservado para la evaluación final y no se usa para ajustar reglas.\n"
              "Si ya terminaste de diseñar las reglas, agrega --evaluacion-final.")
        return 1

    casos = cargar_casos(RAIZ / "benchmark" / "casos" / args.conjunto)
    confusion, errores = Counter(), []
    for _, caso in casos:
        pred = predecir(caso)
        confusion[(caso["categoria"], pred)] += 1
        if pred != caso["categoria"]:
            errores.append((caso["id"], caso["categoria"], pred))

    print(f"Conjunto {args.conjunto.upper()}: {len(casos)} casos\n")
    print("Matriz de confusión (filas = categoría real, columnas = categoría que asigna el diagnóstico)")
    print(f"{'':<9}" + "".join(f"{CORTO[c]:>9}" for c in CATEGORIAS))
    for real in CATEGORIAS:
        print(f"{CORTO[real]:<9}" + "".join(f"{confusion[(real, p)]:>9}" for p in CATEGORIAS))

    filas, macro_f1 = metricas(confusion)
    print(f"\n{'categoría':<10}{'casos':>7}{'precisión':>11}{'recall':>9}{'F1':>7}")
    for cat in CATEGORIAS:
        precision, recall, f1, n = filas[cat]
        print(f"{CORTO[cat]:<10}{n:>7}{precision:>11.2f}{recall:>9.2f}{f1:>7.2f}")
    aciertos = sum(confusion[(c, c)] for c in CATEGORIAS)
    print(f"\nExactitud: {aciertos}/{len(casos)} = {aciertos / len(casos):.2f}   |   macro-F1: {macro_f1:.2f}")
    extra = texto_macro_presentes(filas)
    if extra:
        print(extra)

    if args.conjunto == "dev" and errores:
        print(f"\nCasos mal clasificados ({len(errores)}):")
        for cid, real, pred in errores:
            print(f"  {cid:<8} real: {CORTO[real]:<8} diagnóstico: {CORTO[pred]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
