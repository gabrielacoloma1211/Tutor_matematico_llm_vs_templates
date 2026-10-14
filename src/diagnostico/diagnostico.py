"""
Módulo de diagnóstico determinista.

Responsabilidad única: recibir la discrepancia simbólica reportada por el
verificador y clasificarla en una de las categorías de la taxonomía de
errores, mediante un árbol de decisión. Este módulo NO decide si un paso es
válido (eso ya lo resolvió el verificador) ni genera ninguna retroalimentación
en lenguaje natural (eso lo hace el generador).

Árbol de decisión (se evalúan las preguntas en este orden; la primera que se
cumple asigna la categoría):

    1. ¿Falla en un término distribuido?    -> distributiva_incorrecta          
    2. ¿Se operó solo en un lado?           -> operacion_un_lado                
    3. ¿Operación bien, cálculo mal?        -> simplificacion_aritmetica        
    4. ¿Divisor final incorrecto?           -> division_coeficiente_equivocado  
    5. ¿Un término cambió de signo?         -> error_signo                      
    6. Ninguna aplica con claridad          -> indeterminado

Preguntas 1, 2 y 5 ("generar y comprobar"):
  Se simulan posibles errores a partir del paso anterior (S_i) y se comprueba
  si alguno es equivalente al paso del estudiante (S_{i+1}), incluso si
  después realizó operaciones correctas. Para esto se necesita conservar
  la ecuación original, con sus paréntesis y ambos lados de la igualdad.

Preguntas 3 y 4 ("comparar con el paso correcto"):
  Se compara lo que escribió el estudiante con lo que debería haber escrito,
  buscando diferencias en los términos, números o signos.
"""
import json
from dataclasses import dataclass
from pathlib import Path

import sympy as sp

from src.verificador.verificador import Discrepancia, ecuaciones_equivalentes

_RUTA_TAXONOMIA = Path(__file__).resolve().parent.parent.parent / "data" / "taxonomia.json"

@dataclass
class ResultadoDiagnostico:
    categoria_id: str
    detalles: dict

def _cargar_taxonomia():
    with open(_RUTA_TAXONOMIA, encoding="utf-8") as f:
        return json.load(f)

TAXONOMIA = _cargar_taxonomia()

# --------------------------------------------------------------------------
# Utilidades comunes
# --------------------------------------------------------------------------
def _terminos(lado):
    """Sumandos de un lado de la ecuación, con los números ya evaluados."""
    return list(sp.Add.make_args(sp.sympify(lado).doit()))

def _terminos_escritos(lado):
    """
    Términos de un lado tal como los escribió el estudiante: cada sumando
    se evalúa por separado, pero no se combinan entre sí (x/2 - x sigue
    siendo dos términos, x/2 y -x).
    """
    return [sp.sympify(t).doit() for t in sp.Add.make_args(lado)]

def _denominadores_escritos(expr):
    """Denominadores enteros tal como están escritos en la expresión original."""
    return {
        abs(int(n.base))
        for n in sp.preorder_traversal(expr)
        if isinstance(n, sp.Pow) and n.exp == -1 and n.base.is_Integer
    }

# --------------------------------------------------------------------------
# DISTRIBUTIVA INCORRECTA
# --------------------------------------------------------------------------
_DESCRIPCION_DISTRIBUTIVA = {
    "omite_factor": "no multiplicó un término del paréntesis por el factor",
    "signo": "multiplicó un término del paréntesis con el signo equivocado",
    "suma_factor": "sumó el factor a un término en vez de multiplicarlo",
    "suma_magnitudes": "sumó las magnitudes del factor y del término en vez de multiplicarlos",
}


def _factores(nodo):
    """Aplana los productos anidados: (-1) * (4 * (x + 3)) -> [-1, 4, x + 3]."""
    if isinstance(nodo, sp.Mul):
        return [f for a in nodo.args for f in _factores(a)]
    return [nodo]


def _productos_con_parentesis(expr):
    """
    Productos externos 'factor * (t1 + t2 + ...)' de un lado de la ecuación.
    El signo que precede al paréntesis (p. ej. '- 4(x + 3)') queda incluido en el factor.
    """
    if isinstance(expr, sp.Mul) and any(isinstance(f, sp.Add) for f in _factores(expr)):
        return [expr]
    if isinstance(expr, sp.Add):
        return [p for a in expr.args for p in _productos_con_parentesis(a)]
    return []


def _expansiones_erroneas(producto):
    """
    Genera las expansiones erróneas típicas de 'k * (t1 + ... + tn)': en un
    único término tj, el estudiante comete uno de estos errores.
    Devuelve tuplas (tipo_de_error, expansion_erronea, factor_k).
    """
    factores = _factores(producto)
    suma = next(f for f in factores if isinstance(f, sp.Add))
    k = sp.Mul(*[f for f in factores if f is not suma])
    terminos = [sp.sympify(t).doit() for t in suma.args]  #ej. (-1)*4 -> -4

    for j, t in enumerate(terminos):
        def con(nuevo):
            return sp.Add(*[(nuevo if i == j else k * u) for i, u in enumerate(terminos)])

        coef, mono = t.as_coeff_Mul()
        yield "omite_factor", con(t), k # no lo multiplica
        yield "signo", con(-k * t), k # signo equivocado
        if not t.free_symbols:
            # Sumar en vez de multiplicar solo es un error posible con los números
            # del paréntesis (2(x + 4) -> 2x + 6), no con el término de la incógnita.
            yield "suma_factor", con(k + t), k # k + t en vez de k * t
            yield "suma_magnitudes", con(sp.sign(k * coef) * (abs(k) + abs(coef)) * mono), k # |k| + |t|, con el signo de k*t


def _es_distributiva(d: Discrepancia):
    """devuelve un dict con los detalles si la respuesta es sí; si no, None."""
    for nombre, lado, otro in (("izq", d.izq_i, d.der_i), ("der", d.der_i, d.izq_i)):
        for producto in _productos_con_parentesis(lado):
            for tipo, expansion, k in _expansiones_erroneas(producto):
                lado_erroneo = lado.xreplace({producto: expansion})
                izq_w, der_w = (lado_erroneo, otro) if nombre == "izq" else (otro, lado_erroneo)
                if ecuaciones_equivalentes(izq_w, der_w, d.izq_i, d.der_i):
                    continue  # esa "expansión errónea" no cambia la ecuación: no es un error
                if ecuaciones_equivalentes(izq_w, der_w, d.izq_i_mas_1, d.der_i_mas_1):
                    return {
                        "regla": "distributiva_incorrecta",
                        "variante": tipo,
                        "factor": str(k),
                        "explicacion": _DESCRIPCION_DISTRIBUTIVA[tipo],
                    }
    return None


# --------------------------------------------------------------------------
# OPERACIÓN EN UN SOLO LADO
# --------------------------------------------------------------------------
def _lado_intacto(antes, despues):
    """¿Un lado de la ecuación quedó igual en el paso del estudiante?"""
    return sp.simplify(antes - despues) == 0


def _hipotesis_un_lado(d: Discrepancia):
    """
    Genera la ecuación S_i con una operación aplicada en un solo lado:
      - restar o sumar un término de la ecuación (p. ej. quitar el +3 de un lado sin restarlo del
        otro, o sumar el 3 solo en el otro lado);
      - multiplicar por un denominador de la ecuación, o por el mínimo común múltiplo de
        varios, para quitarlos;
      - dividir entre el coeficiente de la incógnita.
    Devuelve tuplas (descripcion, lado_operado, multiplicador, tipo, izq_w, der_w).
    """
    terminos = {}
    for lado in (d.izq_i, d.der_i):
        for t in _terminos_escritos(lado):
            terminos[sp.srepr(t)] = t

    multiplicadores = _denominadores_escritos(d.izq_i) | _denominadores_escritos(d.der_i)
    if len(multiplicadores) > 1:
        # con varios denominadores (x/2 + x/3) se quitan todos multiplicando por su mínimo común múltiplo
        multiplicadores = multiplicadores | {int(sp.ilcm(*multiplicadores))}
    divisores = set()
    for lado in (d.izq_i, d.der_i):
        for t in _terminos(lado):
            coef, mono = t.as_coeff_Mul()
            coef = abs(sp.nsimplify(coef))
            if mono.free_symbols and coef.is_Rational and coef.p != 1:
                divisores.add(int(coef.p))

    for nombre, lado, otro in (("izq", d.izq_i, d.der_i), ("der", d.der_i, d.izq_i)):
        def ensamblar(nuevo):
            return (nuevo, otro) if nombre == "izq" else (otro, nuevo)

        donde = "izquierdo" if nombre == "izq" else "derecho"
        for t in terminos.values():
            yield (f"restó {t} solo en el lado {donde}", nombre, None, "suma_resta", *ensamblar(lado - t))
            yield (f"sumó {t} solo en el lado {donde}", nombre, None, "suma_resta", *ensamblar(lado + t))
        for c in multiplicadores:
            yield (f"multiplicó por {c} solo en el lado {donde}", nombre, c, "multiplica", *ensamblar(lado * c))
        for c in divisores:
            yield (f"dividió entre {c} solo en el lado {donde}", nombre, None, "divide", *ensamblar(lado / c))


def _es_un_lado(d: Discrepancia):
    """
    Condiciones: (a) un lado de S_{i+1} es igual al de S_i (el estudiante no lo
    tocó), y (b) S_{i+1} es equivalente a S_i con una operación aplicada solo
    en el otro lado.
    """
    if _lado_intacto(d.izq_i, d.izq_i_mas_1):
        lado_operado = "der"
    elif _lado_intacto(d.der_i, d.der_i_mas_1):
        lado_operado = "izq"
    else:
        return None  # los dos lados cambiaron entonces no es este tipo de error

    calculo = _es_aritmetica(d)
    es_calculo = bool(calculo and calculo["multiplicador"] == "1")  # simplificación con un número mal calculado

    for descripcion, nombre, multiplicador, tipo, izq_w, der_w in _hipotesis_un_lado(d):
        if nombre != lado_operado:
            continue  # la operación solo puede estar en el lado que el estudiante modificó
        if tipo == "suma_resta" and es_calculo:
            # Cambiar un lado en +3 puede coincidir numéricamente con "sumar 3 en un solo lado",
            # pero si el lado tenía algo por calcular es un error de cálculo
            continue
        if ecuaciones_equivalentes(izq_w, der_w, d.izq_i, d.der_i):
            continue  # si no es un error
        if not ecuaciones_equivalentes(izq_w, der_w, d.izq_i_mas_1, d.der_i_mas_1):
            continue
        if multiplicador is not None:
            # Para decir que "multiplicó por c para quitar el denominador", ese
            # denominador ya no debe aparecer en el lado que escribió el estudiante.
            lado_nuevo = d.izq_i_mas_1 if nombre == "izq" else d.der_i_mas_1
            if multiplicador in _denominadores_escritos(lado_nuevo):
                continue
        return {"regla": "operacion_un_lado", "explicacion": descripcion}
    return None


# --------------------------------------------------------------------------
# ERROR ARITMÉTICO
# --------------------------------------------------------------------------
def _forma(lado):
    """Un lado de la ecuación como {monomio: coeficiente} con los términos ya resueltos"""
    expr = sp.expand(sp.sympify(lado).doit())
    forma = {}
    for t in sp.Add.make_args(expr):
        coef, mono = t.as_coeff_Mul()
        forma[mono] = forma.get(mono, 0) + sp.nsimplify(coef)
    return {m: c for m, c in forma.items() if c != 0}


def _tiene_algo_por_calcular(lado):
    """
    Busca si todavía se puede simplificar (sumar, combinar términos semejantes,
    evaluar una fracción o un paréntesis).
    """
    terminos = sp.Add.make_args(lado)
    if len(terminos) > len(_forma(lado)):  #hay terminos que se pueden simplificar
        return True
    for t in terminos:
        factores = _factores(t)
        if any(isinstance(f, sp.Add) for f in factores):  #una suma dentro de un paréntesis o fracción
            return True
        numeros = [f for f in factores if f != -1 and (f.is_Number or (isinstance(f, sp.Pow) and f.base.is_Number))]
        if len(numeros) < 2:
            continue
        numeradores = [f for f in numeros if not isinstance(f, sp.Pow)]
        denominadores = [f.base for f in numeros if isinstance(f, sp.Pow)]
        if len(numeradores) == 1 and len(denominadores) == 1 and sp.gcd(abs(numeradores[0]), denominadores[0]) == 1:
            continue  # una fracción que ya no se puede reducir, como 5/2
        return True  # un producto o cociente de números escrito, p. ej. 18/6, 8x/2 o 4*3
    return False


def _es_aritmetica(d: Discrepancia):
    """
    El paso del estudiante solo simplifica (suma, resta, combina términos
    semejantes o multiplica ambos lados por un denominador): ningún término
    cambia de lado. Es un error de cálculo si, comparado con el paso correcto,
    tiene los mismos términos en cada lado y exactamente UN número distinto, y
    el lado que cambió tenía algo por calcular (si ya estaba simplificado, por
    ejemplo '11', cambiarlo no puede ser un error de cálculo).
    """
    denominadores = _denominadores_escritos(d.izq_i) | _denominadores_escritos(d.der_i)
    multiplicadores = {1} | denominadores
    if len(denominadores) > 1:
        multiplicadores.add(int(sp.ilcm(*denominadores)))
    original = (_forma(d.izq_i), _forma(d.der_i))
    escrito = (_forma(d.izq_i_mas_1), _forma(d.der_i_mas_1))

    for c in sorted(multiplicadores):
        correcto = (_forma(c * d.izq_i), _forma(c * d.der_i))
        if any(set(correcto[i]) != set(escrito[i]) for i in (0, 1)):
            continue  # algún término cambió de lado o desapareció: no es solo simplificar
        diferencias = [(i, m) for i in (0, 1) for m in correcto[i] if correcto[i][m] != escrito[i][m]]
        if len(diferencias) != 1:
            continue
        i, m = diferencias[0]
        if c != 1 and escrito[i][m] == original[i][m] / c:
            continue  # dividió donde debía multiplicar: es la operación inversa, no un error de cálculo
        if c != 1 and escrito[i][m] == original[i][m]:
            continue  # ese lado quedó igual osea no lo multiplicó, y eso no es un error de cálculo
        if c == 1 and not _tiene_algo_por_calcular(d.izq_i if i == 0 else d.der_i):
            continue  # ese lado ya estaba simplificado: cambiarlo no es un error de cálculo
        lado = "izquierdo" if i == 0 else "derecho"
        return {
            "regla": "simplificacion_aritmetica",
            "multiplicador": str(c),
            "lado": lado,
            "valor_correcto": str(correcto[i][m]),
            "valor_escrito": str(escrito[i][m]),
            "explicacion": f"en el lado {lado}, el número {correcto[i][m]} se calculó como {escrito[i][m]}",
        }
    return None


# --------------------------------------------------------------------------
# DIVISOR INCORRECTO
# --------------------------------------------------------------------------
def _division_escrita(expr, numerador):
    """Si 'expr' está escrito como 'numerador / d' con d entero, devuelve d; si no, None."""
    if not isinstance(expr, sp.Mul):
        return None
    factores = _factores(expr)
    divisores = [f for f in factores if isinstance(f, sp.Pow) and f.exp == -1 and f.base.is_Integer]
    if len(divisores) != 1:
        return None
    resto = [f for f in factores if f is not divisores[0]]
    if sp.Mul(*resto) != numerador:
        return None
    return divisores[0].base


def _es_division(d: Discrepancia):
    """
    Pregunta 4. Devuelve un dict con los detalles si la respuesta es sí; si no, None.

    El paso anterior es 'a x = b' (a entero distinto de 0 y de 1, b un número) y el
    estudiante despeja escribiendo 'x = b / d' con un divisor d que no es a.
    El divisor tiene que estar escrito en el paso: si solo aparece el
    resultado no se puede saber por cuánto dividió.
    """
    for izq, der, izq_n, der_n in (
        (d.izq_i, d.der_i, d.izq_i_mas_1, d.der_i_mas_1),
        (d.der_i, d.izq_i, d.der_i_mas_1, d.izq_i_mas_1),
    ):
        forma_izq, forma_der = _forma(izq), _forma(der)
        incognitas = [m for m in forma_izq if m != 1]
        if len(incognitas) != 1 or len(forma_izq) != 1 or not set(forma_der) <= {1}:
            continue
        x = incognitas[0]
        a, b = forma_izq[x], forma_der.get(1, 0)
        if not a.is_Integer:
            # Con un coeficiente fraccionario (x/2 = 11 -> x = 11/2) el estudiante multiplica un
            # lado y divide el otro: no es "dividir entre un número equivocado". Se deja como
            # indeterminado, igual que en el benchmark.
            continue
        if a == 1 or _forma(izq_n) != {x: 1}:
            continue
        divisor = _division_escrita(der_n, b)
        if divisor is None or divisor == a:
            continue
        return {
            "regla": "division_coeficiente_equivocado",
            "coeficiente": str(a),
            "divisor_usado": str(divisor),
            "explicacion": f"dividió entre {divisor} en vez de dividir entre el coeficiente {a}",
        }
    return None


# --------------------------------------------------------------------------
# ERROR DE SIGNO
# --------------------------------------------------------------------------
def _es_signo(d: Discrepancia):
    """
    Hipótesis: un término t pasó al otro lado de la igualdad sin cambiarle el
    signo (en vez de restarlo en ambos lados, lo sumó en el otro). Se usan los
    términos tal como están escritos en S_i. Solo se contempla un término mal;
    dos errores de signo en el mismo paso quedan como indeterminado.
    """
    for nombre, lado, otro in (("izq", d.izq_i, d.der_i), ("der", d.der_i, d.izq_i)):
        for t in _terminos_escritos(lado):
            lado_w, otro_w = lado - t, otro + t   # t cambia de lado conservando su signo
            izq_w, der_w = (lado_w, otro_w) if nombre == "izq" else (otro_w, lado_w)
            if ecuaciones_equivalentes(izq_w, der_w, d.izq_i, d.der_i):
                continue
            if ecuaciones_equivalentes(izq_w, der_w, d.izq_i_mas_1, d.der_i_mas_1):
                return {
                    "regla": "error_signo",
                    "termino": str(t),
                    "explicacion": f"pasó el término {t} al otro lado sin cambiarle el signo",
                }
    return None


# --------------------------------------------------------------------------
# Punto de entrada
# --------------------------------------------------------------------------
def diagnosticar(discrepancia: Discrepancia) -> ResultadoDiagnostico:
    """
    Punto de entrada del módulo de diagnóstico. Recibe la discrepancia
    reportada por el verificador y devuelve la categoría de error 
    correspondiente según la taxonomía.

    Los detalles solo contienen texto, para que se puedan devolver tal cual
    por la API y usar luego en la generación de la retroalimentación.
    """
    detalles = {"diferencia": discrepancia.diferencia}

    # 1. ¿Falla en un término distribuido?
    respuesta = _es_distributiva(discrepancia)
    if respuesta:
        return ResultadoDiagnostico("distributiva_incorrecta", {**detalles, **respuesta})

    # 2. ¿Se operó solo en un lado?
    respuesta = _es_un_lado(discrepancia)
    if respuesta:
        return ResultadoDiagnostico("operacion_un_lado", {**detalles, **respuesta})

    # 3. ¿Operación bien, cálculo mal?
    respuesta = _es_aritmetica(discrepancia)
    if respuesta:
        return ResultadoDiagnostico("simplificacion_aritmetica", {**detalles, **respuesta})

    # 4. ¿Divisor final incorrecto?
    respuesta = _es_division(discrepancia)
    if respuesta:
        return ResultadoDiagnostico("division_coeficiente_equivocado", {**detalles, **respuesta})

    # 5. ¿Un término cambió de signo?
    respuesta = _es_signo(discrepancia)
    if respuesta:
        return ResultadoDiagnostico("error_signo", {**detalles, **respuesta})

    # 6. Ninguna regla aplica con claridad
    return ResultadoDiagnostico("indeterminado", detalles)


def obtener_categoria(categoria_id: str) -> dict:
    """Devuelve la información completa de una categoría a partir de su id."""
    for categoria in TAXONOMIA["categorias"]:
        if categoria["id"] == categoria_id:
            return categoria
    raise ValueError(f"Categoría desconocida: {categoria_id}")
