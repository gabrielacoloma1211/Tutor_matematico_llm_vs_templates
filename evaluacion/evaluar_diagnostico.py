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
from src.diagnostico.diagnostico import diagnosticar  # noqa: E402
from src.verificador.verificador import verificar_paso  # noqa: E402

CATEGORIAS = [
    "error_signo",
    "distributiva_incorrecta",
    "operacion_un_lado",
    "simplificacion_aritmetica",
    "division_coeficiente_equivocado",
    "indeterminado",
]
CORTO = {
    "error_signo": "SIGNO",
    "distributiva_incorrecta": "DISTRIB",
    "operacion_un_lado": "UNLADO",
    "simplificacion_aritmetica": "ARITM",
    "division_coeficiente_equivocado": "DIV",
    "indeterminado": "INDET",
}


def predecir(caso) -> str:
    """Categoría que asigna el diagnóstico al paso erróneo del caso."""
    k = caso["indice_paso_erroneo"]
    pasos = caso["resolucion_estudiante"]
    resultado = verificar_paso(pasos[k - 1], pasos[k])
    return diagnosticar(resultado.discrepancia).categoria_id


def metricas(confusion):
    """Precisión, recall y F1 por categoría, y macro-F1."""
    filas = {}
    for cat in CATEGORIAS:
        tp = confusion[(cat, cat)]
        fp = sum(confusion[(otra, cat)] for otra in CATEGORIAS if otra != cat)
        fn = sum(confusion[(cat, otra)] for otra in CATEGORIAS if otra != cat)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        filas[cat] = (precision, recall, f1, tp + fn)
    macro_f1 = sum(f[2] for f in filas.values()) / len(CATEGORIAS)
    return filas, macro_f1


def macro_f1_presentes(filas):
    """Macro-F1 solo con las categorías que tienen casos. Devuelve (valor, cuántas categorías, cuáles faltan)."""
    presentes = [c for c in CATEGORIAS if filas[c][3] > 0]
    faltan = [c for c in CATEGORIAS if filas[c][3] == 0]
    valor = sum(filas[c][2] for c in presentes) / len(presentes) if presentes else 0.0
    return valor, len(presentes), faltan


def texto_macro_presentes(filas):
    valor, n, faltan = macro_f1_presentes(filas)
    if not faltan:
        return ""
    nombres = ", ".join(CORTO[c] for c in faltan)
    return (f"macro-F1 solo con las {n} categorías que tienen casos: {valor:.2f} "
            f"(sin casos, no evaluadas: {nombres}; con las 6 categorías la categoría sin casos cuenta F1 = 0)")


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
