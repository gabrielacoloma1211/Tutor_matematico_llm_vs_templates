"""
Mide el módulo de diagnóstico sobre la PRUEBA CIEGA: 100 casos generados por un
LLM que no se usan para ajustar nada, solo para medir.

Reglas de uso:
  - El diagnóstico se congela antes de la medición. Este script calcula una huella
    (sha256) del código del verificador, del diagnóstico y de la taxonomía, y otra
    de los casos, y las guarda junto con el resultado.
  - Las etiquetas (`categoria`) las asigna la autora ANTES de ver lo que responde el
    diagnóstico, y no se cambian después. La huella de los casos lo deja registrado.
  - Si el resultado guardado antes tiene otra huella de código, el script avisa: el
    diagnóstico cambió desde la medición anterior y los números ya no son comparables.
  - Los fallos se informan pero no se usan para cambiar reglas. Un cambio posterior
    se declara como ajuste y la prueba deja de ser ciega.

Uso (desde la raíz del repositorio):
    python evaluacion/evaluar_prueba_ciega.py --medicion-sin-ajuste
    python evaluacion/evaluar_prueba_ciega.py --medicion-sin-ajuste --guardar
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from benchmark.validar_casos import validar_caso  
from evaluacion.evaluar_ampliado import resumen  
from evaluacion.evaluar_diagnostico import CATEGORIAS, CORTO, predecir  

ARCHIVO = RAIZ / "benchmark" / "casos" / "prueba_ciega" / "prueba_ciega.json"
TIPOS = ("variante_nueva", "estructura_nueva", "combinado", "fuera_de_taxonomia")


def _huella(rutas):
    h = hashlib.sha256()
    for r in sorted(rutas):
        h.update(r.relative_to(RAIZ).as_posix().encode())
        h.update(r.read_bytes())
    return h.hexdigest()[:16]


def huella_codigo():
    """Huella del código que se congela: verificador, diagnóstico y taxonomía."""
    rutas = list((RAIZ / "src" / "verificador").glob("*.py")) + list((RAIZ / "src" / "diagnostico").glob("*.py"))
    rutas.append(RAIZ / "data" / "taxonomia.json")
    return _huella(rutas)


def huella_casos():
    return _huella([ARCHIVO])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--medicion-sin-ajuste", action="store_true",
                    help="confirma que esta medición no se usará para ajustar reglas")
    ap.add_argument("--guardar", action="store_true")
    args = ap.parse_args(argv)
    if not args.medicion_sin_ajuste:
        print("La prueba ciega solo mide: los fallos no se usan para cambiar reglas.\n"
              "Para correrla, agrega --medicion-sin-ajuste.")
        return 2

    casos = json.load(open(ARCHIVO, encoding="utf-8"))
    ids = Counter(c.get("id") for c in casos)
    problemas = {c.get("id"): validar_caso(c) for c in casos}
    problemas = {k: v for k, v in problemas.items() if v}
    repetidos = [k for k, n in ids.items() if n > 1]
    if problemas or repetidos:
        for k, v in problemas.items():
            print(f"✗ {k}: " + "; ".join(v))
        for k in repetidos:
            print(f"✗ id repetido: {k}")
        print("\nHay casos que no pasan el validador. Se corrigen antes de medir, sin mirar el diagnóstico.")
        return 1
    sin_tipo = [c["id"] for c in casos if c.get("tipo_de_novedad") not in TIPOS]
    if sin_tipo:
        print(f"Falta tipo_de_novedad (o no es válido) en: {', '.join(sin_tipo)}")
        return 1

    codigo, datos = huella_codigo(), huella_casos()
    d = RAIZ / "evaluacion" / "resultados"
    previos = sorted(d.glob("prueba_ciega_*.txt"))
    aviso = ""
    if previos:
        for linea in previos[-1].read_text(encoding="utf-8").splitlines():
            if linea.startswith("huella del código:") and linea.split(":")[1].strip() != codigo:
                aviso = (f"AVISO: el código cambió desde {previos[-1].name}. "
                         "La prueba dejó de ser ciega respecto a ese resultado.")
            if linea.startswith("huella de los casos:") and linea.split(":")[1].strip() != datos:
                aviso += (f"\nAVISO: los casos o sus etiquetas cambiaron desde {previos[-1].name}.")

    preds = {}
    for c in casos:
        try:
            preds[c["id"]] = predecir(c)
        except Exception as e:
            preds[c["id"]] = "ERROR"
            print(f"AVISO: {c['id']} produjo {type(e).__name__}")

    partes = [f"huella del código: {codigo}\nhuella de los casos: {datos}"]
    if aviso:
        partes.append(aviso)
    partes.append(resumen(casos, preds, "PRUEBA CIEGA"))

    tabla = [f"{'tipo de novedad':<20}{'casos':>6}{'aciertos':>10}{'seguros':>9}{'peligrosos':>12}"]
    for tipo in TIPOS:
        cs = [c for c in casos if c["tipo_de_novedad"] == tipo]
        ac = sum(preds[c["id"]] == c["categoria"] for c in cs)
        seg = sum(preds[c["id"]] != c["categoria"] and preds[c["id"]] in ("indeterminado", "ERROR") for c in cs)
        tabla.append(f"{tipo:<20}{len(cs):>6}{ac:>10}{seg:>9}{len(cs) - ac - seg:>12}")
    partes.append("== Por tipo de novedad (seguro = responde indeterminado o falla sin clasificar; peligroso = otra categoría)\n"
                  + "\n".join(tabla))

    fallos = [f"  {c['id']:<8} tipo {c['tipo_de_novedad']:<18} autora: {CORTO[c['categoria']]:<8} "
              f"diagnóstico: {CORTO.get(preds[c['id']], 'ERROR')}"
              for c in casos if preds[c["id"]] != c["categoria"]]
    partes.append(f"== Casos mal clasificados ({len(fallos)}). Se informan, no se usan para ajustar.\n" + "\n".join(fallos))
    texto = "\n\n".join(partes)
    print(texto)
    if args.guardar:
        d.mkdir(exist_ok=True)
        base = f"prueba_ciega_{date.today().isoformat()}"
        (d / f"{base}.txt").write_text(texto + "\n", encoding="utf-8")
        (d / f"{base}_predicciones.json").write_text(json.dumps(preds, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
