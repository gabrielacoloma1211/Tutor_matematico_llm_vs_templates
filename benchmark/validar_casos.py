"""
Validador de casos del benchmark.

Comprueba la consistencia matemática de cada caso usando el verificador
determinista (src/verificador). Es decir, revisa que:

  1. Todos los pasos de la solución correcta sean transiciones válidas
  2. En la resolución del estudiante, el paso marcado como erróneo sea
     realmente inválido, y todos los demás pasos sean válidos.
  3. La corrección esperada sea una transición válida desde el paso anterior
     al error.
  4. El caso tenga todos los campos y una categoría que exista en la taxonomía.

  5. La ecuación inicial de solucion_correcta sea la del enunciado ("Resuelve: <ecuación>").
  6. El último paso de solucion_correcta sea el despeje de la incógnita ("x = valor") y
     ese valor satisfaga la ecuación inicial.

IMPORTANTE: este validador no asigna ni verifica la categoría de error.
La categoría la establece la autora al elaborar el caso; este
validador solo comprueba la consistencia matemática y no asigna etiquetas.
Más adelante, la categoría que asigne el módulo de diagnóstico se comparará
contra la que escribió la autora.

Uso (desde la raíz del repositorio):
    python benchmark/validar_casos.py                      # valida benchmark/casos/dev
    python benchmark/validar_casos.py benchmark/casos/ejemplos
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import sympy as sp  
from src.verificador.verificador import verificar_paso, parsear_ecuacion, ErrorDeParseo  

CAMPOS_OBLIGATORIOS = [
    "id",
    "categoria",
    "enunciado",
    "solucion_correcta",
    "resolucion_estudiante",
    "indice_paso_erroneo",
    "correccion_esperada",
    "pista_referencia",
]

_CATEGORIAS_POR_DEFECTO = [
    "error_signo",
    "distributiva_incorrecta",
    "operacion_un_lado",
    "simplificacion_aritmetica",
    "division_coeficiente_equivocado",
    "indeterminado",
]

def _cargar_categorias():
    """Lee los ids de categoría desde data/taxonomia.json (si existe)."""
    try:
        with open(RAIZ / "data" / "taxonomia.json", encoding="utf-8") as f:
            return [c["id"] for c in json.load(f)["categorias"]]
    except (OSError, KeyError, ValueError):
        return list(_CATEGORIAS_POR_DEFECTO)


CATEGORIAS = _cargar_categorias()

# Distribución objetivo del conjunto dev (100 casos).
# Criterio: más peso a error de signo (la categoría que la literatura reporta como más 
# frecuente) y a distributiva (la que admite más variantes de error), y al menos 
# ~12 casos por categoría para que el F1 de
# cada una sea interpretable.
OBJETIVO_DEV = {
    "error_signo": 26,
    "distributiva_incorrecta": 20,
    "operacion_un_lado": 14,
    "simplificacion_aritmetica": 14,
    "division_coeficiente_equivocado": 14,
    "indeterminado": 12,
}


_CARACTER_PERMITIDO = re.compile(r"[0-9x+\-*/().=\s]")


def _caracteres_no_permitidos(ecuacion):
    return sorted({c for c in ecuacion if not _CARACTER_PERMITIDO.fullmatch(c)})

# Distribución objetivo del conjunto test (50 casos): la mitad de dev, redondeada
OBJETIVO_TEST = {
    "error_signo": 13,
    "distributiva_incorrecta": 10,
    "operacion_un_lado": 7,
    "simplificacion_aritmetica": 7,
    "division_coeficiente_equivocado": 7,
    "indeterminado": 6,
}


def _revisar_transicion(anterior, siguiente, donde, errores):
    """
    Devuelve True/False según el verificador, o None si la ecuación no se pudo
    interpretar (en ese caso agrega el mensaje a `errores`).

    Antes de verificar se revisan los caracteres: el signo menos "−" o el "×"
    no generan un error de parseo en SymPy, sino una interpretación incorrecta 
    en silencio, por eso se rechazan 
    """
    raros = sorted(set(_caracteres_no_permitidos(anterior)) | set(_caracteres_no_permitidos(siguiente)))
    if raros:
        errores.append(
            f"{donde}: caracteres no permitidos {raros}. Usa solo dígitos, x, + - * / ( ) . = "
            "y espacios (el signo menos debe ser el guion normal '-')"
        )
        return None
    try:
        return verificar_paso(anterior, siguiente).valido
    except ErrorDeParseo as e:
        errores.append(f"{donde}: no se pudo interpretar la ecuación ({e})")
        return None


_ENUNCIADO = re.compile(r"^\s*Resuelve\s*:\s*(.+?)\s*$")


def _revisar_enunciado(caso, sol):
    """El enunciado debe ser 'Resuelve: <ecuación>' y la ecuación debe ser la inicial de la solución."""
    m = _ENUNCIADO.match(caso["enunciado"]) if isinstance(caso["enunciado"], str) else None
    if not m:
        return [f"enunciado ('{caso['enunciado']}') debe tener la forma 'Resuelve: <ecuación>'"]
    del_enunciado = m.group(1).replace(" ", "")
    if del_enunciado != sol[0].replace(" ", ""):
        return [
            f"la ecuación inicial de solucion_correcta ('{sol[0]}') no corresponde al enunciado "
            f"('{m.group(1)}')"
        ]
    return []


def _revisar_despeje(sol):
    """El último paso de la solución debe ser 'x = valor' (o 'valor = x') y el valor debe satisfacer la ecuación inicial."""
    try:
        izq_u, der_u = parsear_ecuacion(sol[-1])
        izq_0, der_0 = parsear_ecuacion(sol[0])
    except ErrorDeParseo:
        return []  # ya se informa en la revisión de transiciones
    x = sp.Symbol("x")
    if izq_u == x and not der_u.free_symbols:
        valor = der_u
    elif der_u == x and not izq_u.free_symbols:
        valor = izq_u
    else:
        return [
            f"el último paso de solucion_correcta ('{sol[-1]}') debe ser el despeje de la incógnita "
            "(por ejemplo 'x = 3'), con la x sola a un lado y un número al otro"
        ]
    # Todo en racionales exactos: con coeficientes decimales (0.3x) el residuo en
    # punto flotante quedaría ~1e-16 aunque el valor sea correcto
    valor = sp.nsimplify(valor.doit(), rational=True)
    dif = sp.nsimplify((izq_0 - der_0).doit(), rational=True)
    residuo = sp.simplify(dif.subs(x, valor).doit())
    if residuo != 0:
        return [
            f"el valor del último paso de solucion_correcta ('{sol[-1]}') no satisface la ecuación "
            f"inicial '{sol[0]}': al reemplazar la x queda una diferencia de {residuo}"
        ]
    return []


def validar_caso(caso, exigir_despeje=True):
    """
    Devuelve la lista de problemas encontrados (lista vacía = caso consistente).

    `exigir_despeje=False` se usa solo para las variaciones, que son un único paso
    y no resuelven la ecuación completa.
    """
    faltan = [c for c in CAMPOS_OBLIGATORIOS if c not in caso]
    if faltan:
        return [f"faltan campos obligatorios: {', '.join(faltan)}"]

    errores = []
    sol = caso["solucion_correcta"]
    est = caso["resolucion_estudiante"]
    idx = caso["indice_paso_erroneo"]

    if caso["categoria"] not in CATEGORIAS:
        errores.append(
            f"categoria '{caso['categoria']}' no existe en la taxonomía "
            f"(opciones: {', '.join(CATEGORIAS)})"
        )
    if not isinstance(sol, list) or len(sol) < 2:
        errores.append("solucion_correcta debe ser una lista de al menos 2 pasos")
    if not isinstance(est, list) or len(est) < 2:
        errores.append("resolucion_estudiante debe ser una lista de al menos 2 pasos")
    if errores:
        return errores
    if not isinstance(idx, int) or isinstance(idx, bool) or not (1 <= idx < len(est)):
        return [
            f"indice_paso_erroneo ({idx!r}) debe ser un entero entre 1 y {len(est) - 1}: "
            "es la posición del paso del estudiante que contiene el error "
            "(el primer paso es la posición 0)"
        ]

    if sol[0].replace(" ", "") != est[0].replace(" ", ""):
        errores.append(
            "el primer paso de solucion_correcta y de resolucion_estudiante "
            "debe ser la misma ecuación"
        )

    # 0. La ecuación inicial corresponde al enunciado
    errores.extend(_revisar_enunciado(caso, sol))

    # 1. Solución correcta: todas las transiciones deben ser válidas
    for i in range(1, len(sol)):
        r = _revisar_transicion(sol[i - 1], sol[i], f"solucion_correcta, paso {i}", errores)
        if r is False:
            errores.append(
                f"solucion_correcta, paso {i}: '{sol[i - 1]}' -> '{sol[i]}' "
                "debería ser válido pero el verificador lo marca inválido"
            )

    # 1b. El último paso de la solución es el despeje y satisface la ecuación inicial
    if exigir_despeje:
        errores.extend(_revisar_despeje(sol))

    # 2. Resolución del estudiante: solo el paso `idx` debe ser inválido
    for i in range(1, len(est)):
        r = _revisar_transicion(est[i - 1], est[i], f"resolucion_estudiante, paso {i}", errores)
        if r is None:
            continue
        if i == idx and r is True:
            errores.append(
                f"resolucion_estudiante, paso {i}: lo marcaste como erróneo pero "
                f"el verificador lo considera VÁLIDO ('{est[i - 1]}' -> '{est[i]}')"
            )
        elif i != idx and r is False:
            errores.append(
                f"resolucion_estudiante, paso {i}: el verificador lo considera inválido, "
                f"pero solo el paso {idx} debería serlo ('{est[i - 1]}' -> '{est[i]}')"
            )

    # 3. La corrección esperada debe ser un paso válido desde antes del error
    r = _revisar_transicion(
        est[idx - 1], caso["correccion_esperada"], "correccion_esperada", errores
    )
    if r is False:
        errores.append(
            f"correccion_esperada: '{est[idx - 1]}' -> '{caso['correccion_esperada']}' "
            "no es un paso válido"
        )
    return errores


def cargar_casos(directorio):
    """Lee todos los *.json de un directorio. Devuelve [(nombre_archivo, caso), ...]."""
    casos = []
    for ruta in sorted(Path(directorio).glob("*.json")):
        try:
            with open(ruta, encoding="utf-8") as f:
                datos = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"{ruta.name}: JSON inválido ({e})") from e
        if not isinstance(datos, list):
            raise ValueError(f"{ruta.name}: debe contener una lista de casos [ {{...}}, {{...}} ]")
        casos.extend((ruta.name, c) for c in datos)
    return casos


def main(argv=None):
    ap = argparse.ArgumentParser(description="Valida la consistencia matemática de los casos del benchmark.")
    ap.add_argument(
        "directorio",
        nargs="?",
        default=str(RAIZ / "benchmark" / "casos" / "dev"),
        help="carpeta con archivos .json de casos (por defecto: benchmark/casos/dev)",
    )
    args = ap.parse_args(argv)

    directorio = Path(args.directorio)
    casos = cargar_casos(directorio)
    if not casos:
        print(f"No hay casos en {directorio}")
        return 0

    problemas = 0
    vistos = Counter(c.get("id") for _, c in casos)
    for archivo, caso in casos:
        errs = validar_caso(caso)
        if vistos[caso.get("id")] > 1:
            errs.append(f"el id '{caso.get('id')}' está repetido")
        etiqueta = f"{archivo}: {caso.get('id', '(sin id)')}"
        if errs:
            problemas += 1
            print(f"✗ {etiqueta}")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"✓ {etiqueta}")

    print(f"\n{len(casos) - problemas}/{len(casos)} casos consistentes")

    objetivos = {"dev": OBJETIVO_DEV, "test": OBJETIVO_TEST}.get(directorio.name)
    if objetivos:
        conteo = Counter(c.get("categoria") for _, c in casos)
        print(f"\nAvance del conjunto {directorio.name} (hechos / objetivo):")
        for cat, objetivo in objetivos.items():
            print(f"  {cat:<34} {conteo.get(cat, 0):>3} / {objetivo}")
        print(f"  {'TOTAL':<34} {len(casos):>3} / {sum(objetivos.values())}")

    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
