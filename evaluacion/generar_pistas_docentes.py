"""
Genera las pistas que se entregan a los docentes y deja la evaluación pareada y ciega.

Para cada uno de los 30 casos de la hoja (evaluacion/docentes/PLANTILLA_DOCENTES.md):
  1. obtiene el diagnóstico común (el mismo para las dos pistas);
  2. genera la pista con plantillas y la pista con el LLM, ambas con el paso anterior y el paso del estudiante;
  3. guarda las dos pistas ORIGINALES en pistas_originales.json (con la configuración del LLM) y no las vuelve
     a escribir nunca: si el archivo existe, solo se generan las que falten;
  4. asigna al azar, con semilla fija, cuál será la pista A y cuál la B (15 y 15 con el LLM como A);
  5. guarda esa correspondencia aparte, en CLAVE_AB_no_entregar.json (no se entrega a los docentes);
  6. escribe HOJAS_DOCENTES_con_pistas.md: la plantilla con las pistas A y B en su lugar, sin decir su origen.

Las pistas no se editan a mano. Si alguna incumple el formato o parece revelar la solución, el informe final la
señala y se decide qué hacer dejando constancia; el script no la corrige ni la reemplaza.

Uso:
    python evaluacion/generar_pistas_docentes.py --solo-comprobar   # sin LLM: revisa los casos y el diagnóstico
    python evaluacion/generar_pistas_docentes.py                    # genera todo (usa la clave de .env)
    python evaluacion/generar_pistas_docentes.py --reintentar       # vuelve a llamar solo a los casos que fallaron
"""
import argparse
import subprocess
import json
import random
import re
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from evaluacion.comun import configuracion_experimento
from evaluacion.piloto_modelos import revela_solucion
from src.diagnostico.diagnostico import diagnosticar
from src.generador import llm
from src.generador.plantillas import generar_retroalimentacion_plantilla
from src.verificador.verificador import verificar_paso

SEMILLA = 20261107
CARPETA = RAIZ / "evaluacion" / "docentes"
SELECCION = RAIZ / "benchmark" / "casos" / "evaluacion_docente" / "seleccion_30.json"
_CASO = re.compile(
    r"### Caso (\d+)\s+- Ejercicio: (.+?)\s+- Paso anterior: (.+?)\s+- Paso del estudiante \(con un error\): (.+?)\s*\n",
    re.DOTALL)


def _sin_formato(texto: str) -> str:
    """Quita las marcas de Markdown (escapes y comillas) que pandoc agrega al convertir el Word."""
    return texto.replace("\\", "").replace("`", "").strip()


def leer_casos_de_la_hoja(texto_md: str, seleccion: list[dict]) -> list[tuple[int, dict]]:
    """Empareja cada 'Caso k' de la hoja con su caso de seleccion_30.json (por enunciado y pasos)."""
    por_clave = {(c["enunciado"], c["paso_anterior"], c["paso_erroneo"]): c for c in seleccion}
    encontrados = []
    for numero, enunciado, anterior, erroneo in _CASO.findall(texto_md):
        clave = (_sin_formato(enunciado), _sin_formato(anterior), _sin_formato(erroneo))
        if clave not in por_clave:
            raise SystemExit(f"El Caso {numero} de la hoja no coincide con ningún caso de seleccion_30.json: {clave}")
        encontrados.append((int(numero), por_clave[clave]))
    ids = [c["id"] for _, c in encontrados]
    if len(encontrados) != len(seleccion) or len(set(ids)) != len(ids):
        raise SystemExit(f"La hoja tiene {len(encontrados)} casos ({len(set(ids))} distintos); se esperaban {len(seleccion)}.")
    return encontrados


def diagnostico_comun(caso: dict):
    res = diagnosticar(verificar_paso(caso["paso_anterior"], caso["paso_erroneo"]).discrepancia)
    if res.categoria_id != caso["categoria"]:
        raise SystemExit(f"{caso['id']}: el diagnóstico da {res.categoria_id} y la selección dice {caso['categoria']}.")
    return res


def _revision(texto: str, caso: dict, res) -> dict:
    return {"incumplimientos": llm.revisar_formato(texto),
            "revela_solucion": revela_solucion(texto, caso, res.detalles.get("valor_correcto", ""))}


def _generar_llm(caso: dict, res, cliente) -> dict:
    try:
        r = llm.generar_retroalimentacion_llm(res, caso["paso_anterior"], caso["paso_erroneo"], cliente=cliente)
    except llm.LLMNoDisponible as e:
        return {"error": str(e)[:300]}
    return {"texto": r.texto, "modelo": r.modelo, "tokens_entrada": r.tokens_entrada,
            "tokens_salida": r.tokens_salida, "latencia_ms": round(r.latencia_ms), "motivo_fin": r.motivo_fin,
            "generada": datetime.now().isoformat(timespec="seconds"), **_revision(r.texto, caso, res)}


def asignar_ab(ids: list[str], semilla: int = SEMILLA) -> dict:
    """Para cada caso, qué mecanismo es la pista A: mitad (15) con el LLM como A y mitad con la plantilla."""
    mitad = len(ids) // 2
    llm_es_a = [True] * mitad + [False] * (len(ids) - mitad)
    random.Random(semilla).shuffle(llm_es_a)
    return {cid: {"A": "llm" if a else "plantilla", "B": "plantilla" if a else "llm"}
            for cid, a in zip(ids, llm_es_a)}


def _escapar(texto: str) -> str:
    return texto.replace("*", "\\*").replace("_", "\\_")


def armar_hoja(texto_md: str, casos: list[tuple[int, dict]], originales: dict, clave: dict) -> str:
    """La hoja con las pistas en su lugar. No dice cuál es de cada mecanismo."""
    bloques = re.split(r"(?=### Caso \d+\n)", texto_md)
    salida = [bloques[0]]
    por_numero = {n: c for n, c in casos}
    for bloque in bloques[1:]:
        n = int(re.match(r"### Caso (\d+)", bloque).group(1))
        cid = por_numero[n]["id"]
        for letra in ("A", "B"):
            mecanismo = clave[cid][letra]
            pista = originales["casos"][cid][mecanismo]["texto"]
            bloque, cuantos = re.subn(rf"\\\[pegar la pista {letra}\\\]|\[pegar la pista {letra}\]",
                                      lambda _m: _escapar(pista), bloque, count=1)
            if cuantos != 1:
                raise SystemExit(f"Caso {n}: no encontré el marcador de la pista {letra}.")
        salida.append(bloque)
    return "".join(salida)


# Lo que debe ser idéntico entre la primera ejecución y las que la reanudan. La fecha es lo único que puede cambiar.
CAMPOS_DE_CONFIGURACION_IGNORADOS = ("fecha",)


def diferencias_de_configuracion(registrada: dict, actual: dict) -> list[str]:
    """Lista legible de lo que cambió entre la configuración registrada al empezar y la actual (vacía si coinciden)."""
    diferencias = []
    for campo in sorted(set(registrada) | set(actual)):
        if campo in CAMPOS_DE_CONFIGURACION_IGNORADOS:
            continue
        antes, ahora = registrada.get(campo), actual.get(campo)
        if campo == "prompts" and isinstance(antes, dict) and isinstance(ahora, dict):
            for nombre in sorted(set(antes) | set(ahora)):
                if antes.get(nombre) != ahora.get(nombre):
                    diferencias.append(f"prompt {nombre}: {antes.get(nombre)} -> {ahora.get(nombre)}")
        elif antes != ahora:
            diferencias.append(f"{campo}: {antes} -> {ahora}")
    return diferencias


ARCHIVOS_PRIVADOS = ("pistas_originales.json", "CLAVE_AB_no_entregar.json", "HOJAS_DOCENTES_con_pistas.md")


def comprobar_que_no_se_suben(carpeta: Path) -> None:
    """Si la carpeta está dentro de un repositorio de Git, exige que los archivos privados estén en .gitignore.

    Estos archivos permiten saber qué mecanismo escribió cada pista: si llegaran al repositorio público se perdería
    el cegamiento. Fuera de un repositorio (o sin Git instalado) no hace nada.
    """
    try:
        dentro = subprocess.run(["git", "-C", str(carpeta), "rev-parse", "--is-inside-work-tree"],
                                capture_output=True, text=True)
    except OSError:
        return
    if dentro.returncode != 0:
        return
    sin_excluir = []
    for nombre in ARCHIVOS_PRIVADOS:
        r = subprocess.run(["git", "-C", str(carpeta), "check-ignore", "-q", str(Path(carpeta) / nombre)])
        if r.returncode != 0:
            sin_excluir.append(nombre)
    if sin_excluir:
        raise SystemExit("Estos archivos revelarían el origen de las pistas y NO están en .gitignore: "
                         + ", ".join(sin_excluir) + ". Agrégalos a .gitignore antes de generar las pistas.")


def main(argv=None, cliente=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--carpeta", type=Path, default=CARPETA)
    ap.add_argument("--solo-comprobar", action="store_true", help="revisa casos y diagnóstico, sin llamar al LLM")
    ap.add_argument("--reintentar", action="store_true", help="vuelve a llamar al LLM en los casos que fallaron")
    args = ap.parse_args(argv)

    comprobar_que_no_se_suben(args.carpeta)
    plantilla = (args.carpeta / "PLANTILLA_DOCENTES.md").read_text(encoding="utf-8")
    seleccion = json.loads(SELECCION.read_text(encoding="utf-8"))
    casos = leer_casos_de_la_hoja(plantilla, seleccion)
    diagnosticos = {c["id"]: diagnostico_comun(c) for _, c in casos}
    print(f"{len(casos)} casos de la hoja emparejados con la selección; diagnóstico coincide en todos.")
    if args.solo_comprobar:
        return 0

    ruta_originales = args.carpeta / "pistas_originales.json"
    originales = (json.loads(ruta_originales.read_text(encoding="utf-8")) if ruta_originales.exists()
                  else {"configuracion": None, "casos": {}})
    if cliente is None:
        try:
            cliente = llm._crear_cliente()
        except llm.LLMNoDisponible as e:
            raise SystemExit(f"No se puede llamar al LLM: {e}")
    actual = configuracion_experimento()
    if originales["configuracion"] is None:
        originales["configuracion"] = actual
        if actual.get("cambios_sin_guardar"):
            print("AVISO: hay cambios sin guardar en Git; el commit registrado no describe exactamente el código usado. "
                  "Haz commit antes de generar las pistas definitivas.")
    else:
        diferencias = diferencias_de_configuracion(originales["configuracion"], actual)
        if diferencias:
            raise SystemExit(
                "La configuración cambió desde que se empezaron a generar las pistas; no se reanuda para no mezclar "
                "respuestas obtenidas en condiciones distintas:\n  - " + "\n  - ".join(diferencias)
                + "\nVuelve a la configuración original (mismo commit y mismos prompts) o, si el cambio es intencional, "
                "empieza de nuevo borrando pistas_originales.json y CLAVE_AB_no_entregar.json (se genera un juego nuevo).")

    for numero, caso in casos:
        cid = caso["id"]
        reg = originales["casos"].setdefault(cid, {
            "numero_en_hoja": numero, "categoria": caso["categoria"], "enunciado": caso["enunciado"],
            "paso_anterior": caso["paso_anterior"], "paso_erroneo": caso["paso_erroneo"]})
        if "plantilla" not in reg:
            texto = generar_retroalimentacion_plantilla(diagnosticos[cid], caso["paso_anterior"], caso["paso_erroneo"])
            reg["plantilla"] = {"texto": texto, **_revision(texto, caso, diagnosticos[cid])}
        if "llm" not in reg or ("error" in reg["llm"] and args.reintentar):
            reg["llm"] = _generar_llm(caso, diagnosticos[cid], cliente)
            print(f"Caso {numero:>2} ({cid}): " + (reg["llm"].get("error") or "pista del LLM guardada"))
        ruta_originales.write_text(json.dumps(originales, ensure_ascii=False, indent=2), encoding="utf-8")

    fallaron = [cid for cid, r in originales["casos"].items() if "error" in r["llm"]]
    if fallaron:
        print(f"\nFaltan las pistas del LLM de {len(fallaron)} casos: {', '.join(fallaron)}. "
              "Corre de nuevo con --reintentar. No se creó la clave A/B ni la hoja.")
        return 1

    ruta_clave = args.carpeta / "CLAVE_AB_no_entregar.json"
    if ruta_clave.exists():
        clave = json.loads(ruta_clave.read_text(encoding="utf-8"))["asignacion"]
    else:
        clave = asignar_ab([c["id"] for _, c in casos])
        ruta_clave.write_text(json.dumps(
            {"aviso": "NO ENTREGAR A LOS DOCENTES: dice qué pista (A o B) salió de qué mecanismo.",
             "semilla": SEMILLA, "asignacion": clave}, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.carpeta / "HOJAS_DOCENTES_con_pistas.md").write_text(
        armar_hoja(plantilla, casos, originales, clave), encoding="utf-8")

    print("\n== Revisión automática de las pistas (no se corrige nada; si algo sale aquí, se decide y se deja constancia)")
    marcadas = 0
    for numero, caso in casos:
        for mecanismo in ("llm", "plantilla"):
            r = originales["casos"][caso["id"]][mecanismo]
            if r["incumplimientos"] or r["revela_solucion"]:
                marcadas += 1
                print(f"  Caso {numero:>2} ({caso['id']}) {mecanismo}: incumplimientos={r['incumplimientos']}, "
                      f"parece revelar la solución={r['revela_solucion']}")
    print(f"  {marcadas} pistas marcadas de {2 * len(casos)}.")
    print(f"\nGuardado en {args.carpeta}: pistas_originales.json, CLAVE_AB_no_entregar.json, HOJAS_DOCENTES_con_pistas.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
