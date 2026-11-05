"""
Piloto para elegir el modelo de LLM que redacta las pistas, ANTES de congelar el prototipo.

Usa los 20 casos de benchmark/casos/evaluacion_docente/piloto_20.json (distintos de los 30 de la evaluación
docente). Para cada modelo genera la pista de cada caso con el mismo código y los mismos parámetros que usa el
prototipo (src/generador/llm.py, solo cambia el modelo) y registra: la pista, la latencia, los tokens y el costo,
y revisa automáticamente tres cosas:
  - la pista no contiene la corrección esperada ni el valor correcto (no revela la solución);
  - la pista es breve (hasta 60 palabras) y está en español (no vacía);
  - la llamada funcionó.
También escribe una hoja de lectura ciega: las pistas de todos los modelos mezcladas, con un código, para que
una persona las lea sin saber de qué modelo salió cada una. La clave está en el JSON de resultados.

Uso:
    export ANTHROPIC_API_KEY="..."
    python evaluacion/piloto_modelos.py --guardar
    python evaluacion/piloto_modelos.py --modelos claude-haiku-5-5 --max-casos 3     # prueba rápida
"""
import argparse
import json
import random
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.diagnostico.diagnostico import diagnosticar  # noqa: E402
from src.generador import llm  # noqa: E402
from src.generador.plantillas import generar_retroalimentacion_plantilla  # noqa: E402
from src.verificador.verificador import verificar_paso  # noqa: E402

# USD por millón de tokens (entrada, salida). Verificar en la página oficial de precios de Anthropic.
PRECIOS = {"claude-sonnet-5-5": (2.00, 10.00), "claude-haiku-5-5": (0.10, 0.50)}
MODELOS_POR_DEFECTO = ["claude-sonnet-5-5", "claude-haiku-5-5"]
MAX_PALABRAS = 60
CASOS = RAIZ / "benchmark" / "casos" / "evaluacion_docente" / "piloto_20.json"


def _sin_espacios(texto: str) -> str:
    return re.sub(r"\s+", "", texto).replace("*", "")


def revela_solucion(pista: str, caso: dict, valor_correcto: str = "") -> bool:
    """¿La pista escribe la corrección esperada o el valor correcto?"""
    p = _sin_espacios(pista)
    if _sin_espacios(caso["correccion_esperada"]) in p:
        return True
    v = _sin_espacios(str(valor_correcto))
    return bool(v) and re.search(rf"(?<![\d.]){re.escape(v)}(?!\d|\.\d)", p) is not None


def costo(modelo: str, entrada: int | None, salida: int | None) -> float | None:
    if modelo not in PRECIOS or entrada is None or salida is None:
        return None
    pe, ps = PRECIOS[modelo]
    return (entrada * pe + salida * ps) / 1_000_000


def generar(modelo: str, caso: dict, cliente) -> dict:
    llm.MODELO = modelo
    res = diagnosticar(verificar_paso(caso["paso_anterior"], caso["paso_erroneo"]).discrepancia)
    fila = {"caso": caso["id"], "categoria": caso["categoria"], "modelo": modelo,
            "diagnostico": res.categoria_id, "pista": None, "error": None}
    try:
        r = llm.generar_retroalimentacion_llm(res, caso["paso_anterior"], caso["paso_erroneo"], cliente=cliente)
    except llm.LLMNoDisponible as e:
        causa = f"{type(e.__cause__).__name__}: {e.__cause__}" if e.__cause__ else str(e)
        fila["error"] = (str(e) + " | " + causa)[:400]
        return fila
    fila.update(pista=r.texto, motivo_fin=r.motivo_fin, tipos_bloque=list(r.tipos_bloque), latencia_ms=round(r.latencia_ms), tokens_entrada=r.tokens_entrada,
                tokens_salida=r.tokens_salida, costo_usd=costo(modelo, r.tokens_entrada, r.tokens_salida))
    fila["revela_solucion"] = revela_solucion(r.texto, caso, res.detalles.get("valor_correcto", ""))
    fila["palabras"] = len(r.texto.split())
    fila["muy_larga"] = fila["palabras"] > MAX_PALABRAS
    fila["cortada"] = r.motivo_fin == "max_tokens"
    return fila


def main(argv=None, cliente=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelos", nargs="+", default=MODELOS_POR_DEFECTO)
    ap.add_argument("--max-casos", type=int, default=None, help="para una prueba rápida")
    ap.add_argument("--max-tokens", type=int, default=None, help="sobrescribe llm.MAX_TOKENS")
    ap.add_argument("--ver-pistas", action="store_true", help="imprime las pistas (rompe la lectura ciega)")
    ap.add_argument("--guardar", action="store_true")
    args = ap.parse_args(argv)

    if args.max_tokens:
        llm.MAX_TOKENS = args.max_tokens
    casos = json.loads(CASOS.read_text(encoding="utf-8"))[: args.max_casos]
    if cliente is None:
        cliente = llm._crear_cliente()
    filas = []
    for modelo in args.modelos:
        for caso in casos:
            f = generar(modelo, caso, cliente)
            filas.append(f)
            estado = f["error"] or f"{f['latencia_ms']} ms, {f['tokens_entrada']}+{f['tokens_salida']} tokens, fin={f['motivo_fin']}, bloques={f['tipos_bloque']}" + (f"\n    -> {f['pista']}" if args.ver_pistas else "")
            print(f"{modelo:<20} {caso['id']:<10} {estado}")

    # resumen por modelo
    print("\n== Resumen por modelo")
    resumen = {}
    for modelo in args.modelos:
        fs = [f for f in filas if f["modelo"] == modelo]
        ok = [f for f in fs if not f["error"]]
        r = {"llamadas": len(fs), "fallaron": len(fs) - len(ok),
             "revelan_solucion": sum(f["revela_solucion"] for f in ok),
             "muy_largas": sum(f["muy_larga"] for f in ok),
             "cortadas": sum(f["cortada"] for f in ok),
             "latencia_media_ms": round(sum(f["latencia_ms"] for f in ok) / len(ok)) if ok else None,
             "costo_total_usd": round(sum(f["costo_usd"] or 0 for f in ok), 4)}
        resumen[modelo] = r
        print(modelo, r)

    if args.guardar:
        salida = RAIZ / "evaluacion" / "resultados" / "piloto_llm"
        salida.mkdir(parents=True, exist_ok=True)
        base = f"piloto_modelos_{date.today().isoformat()}"
        (salida / f"{base}.json").write_text(json.dumps(
            {"parametros": {"temperatura": llm.TEMPERATURA, "max_tokens": llm.MAX_TOKENS},
             "resumen": resumen, "filas": filas}, ensure_ascii=False, indent=2), encoding="utf-8")
        # hoja de lectura ciega: pistas mezcladas, sin el nombre del modelo
        rnd = random.Random(7)
        ok = [f for f in filas if not f["error"]]
        rnd.shuffle(ok)
        lineas = ["# Piloto: lectura ciega de pistas", "",
                  "Califica cada pista de 1 a 5 en: correcta, clara, adecuada para noveno, útil sin dar la solución.", ""]
        clave = {}
        for i, f in enumerate(ok, 1):
            cod = f"P{i:03d}"
            clave[cod] = {"caso": f["caso"], "modelo": f["modelo"]}
            caso = next(c for c in casos if c["id"] == f["caso"])
            lineas += [f"## {cod}", f"- Ejercicio: {caso['enunciado']}",
                       f"- Paso anterior: `{caso['paso_anterior']}`", f"- Paso del estudiante: `{caso['paso_erroneo']}`",
                       f"- Pista: {f['pista']}", "- Notas (c/cl/ad/ut): ", ""]
        (salida / f"{base}_lectura_ciega.md").write_text("\n".join(lineas), encoding="utf-8")
        (salida / f"{base}_clave.json").write_text(json.dumps(clave, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nGuardado en evaluacion/resultados/piloto_llm/{base}*. No abras la clave hasta terminar de leer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
