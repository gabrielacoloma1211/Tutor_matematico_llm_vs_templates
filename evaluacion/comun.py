"""
Funciones que comparten los scripts de evaluación: la categoría que asigna el diagnóstico,
las métricas, el resumen de resultados y el guardado con fecha.

Estaban repartidas entre evaluar_diagnostico.py y evaluar_ampliado.py (un script importaba a otro);
aquí viven en un solo lugar y los scripts solo arman su propio informe.
"""
import hashlib
import json
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path

from src.diagnostico.diagnostico import diagnosticar
from src.verificador.verificador import verificar_paso

RAIZ = Path(__file__).resolve().parent.parent
DIR_RESULTADOS = RAIZ / "evaluacion" / "resultados"

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
TIPOS_DE_NOVEDAD = ("variante_nueva", "estructura_nueva", "combinado", "fuera_de_taxonomia")


def _commit_actual():
    """Commit del repositorio (y si hay cambios sin guardar), o None si no se puede consultar git."""
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True,
                                text=True, timeout=10, check=True).stdout.strip()
        sucio = bool(subprocess.run(["git", "status", "--porcelain"], cwd=RAIZ, capture_output=True,
                                    text=True, timeout=10, check=True).stdout.strip())
    except (OSError, subprocess.SubprocessError):
        return {"commit": None, "cambios_sin_guardar": None}
    return {"commit": commit, "cambios_sin_guardar": sucio}


def configuracion_experimento(prompts=None):
    """Lo que hace reproducible una corrida con el LLM: modelo exacto, parámetros, versión de cada
    prompt (huella SHA-256 de su texto), fecha y commit. Se guarda junto a los resultados."""
    from src.generador import llm  # import tardío: los scripts del diagnóstico no necesitan el LLM
    rutas = [Path(p) for p in (prompts or [llm.RUTA_PROMPT])]
    return {
        "fecha": date.today().isoformat(),
        "modelo": llm.MODELO,
        "temperatura": llm.TEMPERATURA,   # None = no se envía (los modelos 5.x la rechazan)
        "max_tokens": llm.MAX_TOKENS,
        "timeout_segundos": llm.TIMEOUT_SEGUNDOS,
        "prompts": {r.name: hashlib.sha256(r.read_bytes()).hexdigest()[:16] for r in rutas},
        **_commit_actual(),
    }


def predecir(caso) -> str:
    """Categoría que asigna el diagnóstico al paso erróneo del caso."""
    k = caso["indice_paso_erroneo"]
    pasos = caso["resolucion_estudiante"]
    resultado = verificar_paso(pasos[k - 1], pasos[k])
    return diagnosticar(resultado.discrepancia).categoria_id


def predecir_todos(casos):
    """Diccionario id -> categoría. Si el diagnóstico falla se registra como ERROR y se avisa."""
    preds = {}
    for c in casos:
        try:
            preds[c["id"]] = predecir(c)
        except Exception as e:  # el diagnóstico falló: se registra como ERROR, no se oculta
            preds[c["id"]] = "ERROR"
            print(f"AVISO: {c['id']} produjo {type(e).__name__}")
    return preds


def metricas(confusion):
    """Precisión, recall y F1 por categoría, y macro-F1."""
    filas = {}
    for cat in CATEGORIAS:
        tp = confusion[(cat, cat)]
        fp = sum(confusion[(otra, cat)] for otra in CATEGORIAS if otra != cat)
        # fn: todo caso de la categoría real que no se predijo como ella, incluido ERROR (una excepción del
        # diagnóstico), que no es una de las seis categorías pero sí es un fallo.
        fn = sum(cantidad for (real, predicha), cantidad in confusion.items()
                 if real == cat and predicha != cat)
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


def resumen(casos, preds, titulo):
    confusion = Counter((c["categoria"], preds[c["id"]]) for c in casos)
    filas, macro = metricas(confusion)
    ok = sum(confusion[(k, k)] for k in CATEGORIAS)
    out = [f"== {titulo}: {len(casos)} casos | exactitud {ok}/{len(casos)} = {ok/len(casos):.2f} | macro-F1 {macro:.2f}"]
    # la columna ERROR (el diagnóstico lanzó una excepción) solo aparece si hubo alguna
    columnas = CATEGORIAS + (["ERROR"] if any(p == "ERROR" for _, p in confusion) else [])
    out.append(f"{'':<9}" + "".join(f"{CORTO.get(c, c):>8}" for c in columnas))
    for real in CATEGORIAS:
        out.append(f"{CORTO[real]:<9}" + "".join(f"{confusion[(real, p)]:>8}" for p in columnas))
    out.append(f"{'categoría':<10}{'casos':>6}{'prec':>7}{'recall':>8}{'F1':>6}")
    for cat in CATEGORIAS:
        p, r, f, n = filas[cat]
        out.append(f"{CORTO[cat]:<10}{n:>6}{p:>7.2f}{r:>8.2f}{f:>6.2f}")
    extra = texto_macro_presentes(filas)
    if extra:
        out.append(extra)
    return "\n".join(out)


def tabla_por_novedad(casos, preds):
    """Fallos por tipo de novedad: seguros (dice indeterminado) o peligrosos (otra categoría)."""
    tabla = [f"{'tipo de novedad':<20}{'casos':>6}{'aciertos':>10}{'seguros':>9}{'peligrosos':>12}"]
    for tipo in TIPOS_DE_NOVEDAD:
        cs = [c for c in casos if c["tipo_de_novedad"] == tipo]
        ac = sum(preds[c["id"]] == c["categoria"] for c in cs)
        seg = sum(preds[c["id"]] != c["categoria"] and preds[c["id"]] in ("indeterminado", "ERROR") for c in cs)
        tabla.append(f"{tipo:<20}{len(cs):>6}{ac:>10}{seg:>9}{len(cs) - ac - seg:>12}")
    return ("== Por tipo de novedad (seguro = responde indeterminado o falla sin clasificar; peligroso = otra categoría)\n"
            + "\n".join(tabla))


def lista_de_fallos(casos, preds, nota=""):
    fallos = [f"  {c['id']:<8} tipo {c['tipo_de_novedad']:<18} autora: {CORTO[c['categoria']]:<8} "
              f"diagnóstico: {CORTO.get(preds[c['id']], 'ERROR')}"
              for c in casos if preds[c["id"]] != c["categoria"]]
    return f"== Casos mal clasificados ({len(fallos)}){nota}\n" + "\n".join(fallos)


def guardar_resultado(carpeta, base, texto, preds):
    """Guarda en evaluacion/resultados/<carpeta> el informe (.txt) y las predicciones (.json) con el nombre dado."""
    destino = DIR_RESULTADOS / carpeta
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"{base}.txt").write_text(texto + "\n", encoding="utf-8")
    (destino / f"{base}_predicciones.json").write_text(
        json.dumps(preds, indent=2, ensure_ascii=False), encoding="utf-8")
