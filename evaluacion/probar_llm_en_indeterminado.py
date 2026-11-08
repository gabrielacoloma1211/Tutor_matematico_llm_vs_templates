"""
Prueba: ¿qué hace el LLM si se lo llama cuando el diagnóstico es `indeterminado`?

Hipótesis: si el diagnóstico es `indeterminado` (no sabemos qué error fue, o hay varios en un mismo paso), el LLM
podría igual inventar una causa concreta y dársela al estudiante como si fuera cierta. Si eso pasa, es una razón
para no llamarlo en ese caso (y devolver el mensaje general, como hace hoy `src/generador/llm.py`).

Se usa un prompt propio para este caso (data/prompt_llm_indeterminado.txt) que le dice al LLM, de forma explícita,
que no se conoce la causa y que no debe afirmar ninguna. Es la condición más favorable para el LLM: si aun así
nombra una causa, el problema no es el prompt.

Qué hace:
  - toma los casos cuyo diagnóstico es `indeterminado` de dev, ampliado, ampliado_2 y prueba_ciega
    (no usa los de test, que están reservados para la evaluación final);
  - llama al LLM con el mismo código y los mismos parámetros del prototipo, solo que con
    `llm.LLAMAR_EN_INDETERMINADO = True` y el prompt de indeterminado (ambos solo se cambian dentro de este script);
  - revisa automáticamente si la pista (a) nombra una causa concreta de error, (b) revela la solución;
  - guarda una hoja de lectura donde se ve, junto a cada pista, lo que realmente pasó en el caso (notas),
    para que la autora marque si la pista inventó una causa, cubrió solo uno de los errores o fue honesta.

Uso:
    python evaluacion/probar_llm_en_indeterminado.py --max-casos 3          # prueba rápida
    python evaluacion/probar_llm_en_indeterminado.py --guardar
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from evaluacion.comun import configuracion_experimento
from evaluacion.piloto_modelos import costo, revela_solucion  
from src.diagnostico.diagnostico import diagnosticar  
from src.generador import llm  
from src.verificador.verificador import verificar_paso  

RUTA_PROMPT = RAIZ / "data" / "prompt_llm_indeterminado.txt"
CONJUNTOS = ["dev/indeterminado", "ampliado/ampliado", "ampliado_2/ampliado_2", "prueba_ciega/prueba_ciega"]

# Palabras que delatan que la pista afirma una causa concreta (una de las 5 categorías del sistema).
CAUSAS = {
    "signo": r"\bsigno|cambia(r|s)? de lado|al otro lado|transpon",
    "distributiva": r"distributiv|par[eé]ntesis|multiplica(r|s)? (a )?(cada|todos)",
    "un_lado": r"ambos lados|los dos lados|un solo lado|solo (en )?un lado",
    "aritmetica": r"c[aá]lculo|operaci[oó]n num[eé]rica|suma|resta|aritm[eé]tic",
    "division": r"divid|divisor|coeficiente",
}


def causas_nombradas(pista: str) -> list[str]:
    return [k for k, rx in CAUSAS.items() if re.search(rx, pista, re.IGNORECASE)]


def cargar_casos() -> list[dict]:
    casos = []
    for nombre in CONJUNTOS:
        ruta = RAIZ / "benchmark" / "casos" / f"{nombre}.json"
        for c in json.loads(ruta.read_text(encoding="utf-8")):
            k = c["indice_paso_erroneo"]
            pasos = c["resolucion_estudiante"]
            c = dict(c, conjunto=nombre.split("/")[0], paso_anterior=pasos[k - 1], paso_erroneo=pasos[k])
            res = diagnosticar(verificar_paso(c["paso_anterior"], c["paso_erroneo"]).discrepancia)
            if res.categoria_id == "indeterminado":   # solo los que llegarían al LLM si se quitara la protección
                casos.append(c)
    return casos


def probar(caso: dict, cliente) -> dict:
    res = diagnosticar(verificar_paso(caso["paso_anterior"], caso["paso_erroneo"]).discrepancia)
    fila = {"caso": caso["id"], "conjunto": caso["conjunto"], "enunciado": caso["enunciado"],
            "paso_anterior": caso["paso_anterior"], "paso_erroneo": caso["paso_erroneo"],
            "notas": caso.get("notas", ""), "pista": None, "error": None}
    try:
        r = llm.generar_retroalimentacion_llm(res, caso["paso_anterior"], caso["paso_erroneo"], cliente=cliente)
    except llm.LLMNoDisponible as e:
        fila["error"] = str(e)[:300]
        return fila
    fila.update(pista=r.texto, llamo_al_llm=r.usado_llm, tokens_entrada=r.tokens_entrada,
                tokens_salida=r.tokens_salida, costo_usd=costo(r.modelo, r.tokens_entrada, r.tokens_salida),
                causas_nombradas=causas_nombradas(r.texto), incumplimientos=list(r.incumplimientos),
                revela_solucion=revela_solucion(r.texto, caso, res.detalles.get("valor_correcto", "")))
    fila["nombra_causa"] = bool(fila["causas_nombradas"])
    return fila


def main(argv=None, cliente=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-casos", type=int, default=None, help="para una prueba rápida")
    ap.add_argument("--guardar", action="store_true")
    args = ap.parse_args(argv)

    casos = cargar_casos()[: args.max_casos]
    print(f"{len(casos)} casos con diagnóstico indeterminado (modelo {llm.MODELO}).")
    llm.LLAMAR_EN_INDETERMINADO = True      # solo dentro de esta prueba sino False
    llm.PROMPT_SISTEMA = RUTA_PROMPT.read_text(encoding="utf-8")
    if cliente is None:
        cliente = llm._crear_cliente()
    filas = []
    for c in casos:
        f = probar(c, cliente)
        filas.append(f)
        print(f"{c['id']:<10}", f["error"] or f"causas nombradas: {f['causas_nombradas'] or 'ninguna'}"
              + (" | REVELA" if f.get("revela_solucion") else ""))

    ok = [f for f in filas if not f["error"]]
    resumen = {"casos": len(filas), "fallaron": len(filas) - len(ok),
               "nombran_una_causa": sum(f["nombra_causa"] for f in ok),
               "revelan_solucion": sum(f["revela_solucion"] for f in ok),
               "costo_total_usd": round(sum(f["costo_usd"] or 0 for f in ok), 4)}
    print("\n== Resumen\n", resumen)

    if args.guardar:
        salida = RAIZ / "evaluacion" / "resultados" / "indeterminado_con_llm"
        salida.mkdir(parents=True, exist_ok=True)
        base = f"indeterminado_con_llm_{date.today().isoformat()}"
        (salida / f"{base}.json").write_text(json.dumps(
            {"configuracion": configuracion_experimento([RUTA_PROMPT]), "modelo": llm.MODELO,
             "resumen": resumen, "filas": filas}, ensure_ascii=False, indent=2), encoding="utf-8")
        lineas = ["# El LLM llamado en casos indeterminados: hoja de lectura", "",
                  "Para cada caso marca: (a) la pista inventa una causa que no es la real; (b) menciona solo uno de los "
                  "errores; (c) es honesta y no afirma una causa; (d) revela la solución.", ""]
        for f in ok:
            lineas += [f"## {f['caso']} ({f['conjunto']})", f"- Ejercicio: {f['enunciado']}",
                       f"- Paso anterior: `{f['paso_anterior']}`", f"- Paso del estudiante: `{f['paso_erroneo']}`",
                       f"- Lo que realmente pasó: {f['notas']}", f"- Pista del LLM: {f['pista']}",
                       f"- Causas que nombra (automático): {', '.join(f['causas_nombradas']) or 'ninguna'}",
                       "- Marca (a/b/c/d): ", ""]
        (salida / f"{base}_lectura.md").write_text("\n".join(lineas), encoding="utf-8")
        print(f"\nGuardado en evaluacion/resultados/indeterminado_con_llm/{base}*")
    return 0


if __name__ == "__main__":
    sys.exit(main())
