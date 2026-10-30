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
import re
from collections import Counter
from fractions import Fraction
from dataclasses import dataclass
from pathlib import Path

import sympy as sp

from src.verificador.verificador import Discrepancia, ecuaciones_equivalentes, parsear_ecuacion

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
    """Términos (sumandos) de un lado de la ecuación, con los números ya evaluados."""
    return list(sp.Add.make_args(sp.sympify(lado).doit()))


def _terminos_escritos(lado):
    """
    Términos de un lado tal como los escribió el estudiante: cada sumando
    se evalúa por separado, pero NO se combinan entre sí (x/2 - x sigue
    siendo dos términos, x/2 y -x).
    """
    return [sp.sympify(t).doit() for t in sp.Add.make_args(lado)]


def _denominadores_escritos(expr):
    """Denominadores enteros tal como están escritos en la expresión original (no simplificada)."""
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
    "agrega_incognita": "al multiplicar un número por el factor le agregó una incógnita que no tenía",
    "pierde_incognita": "al multiplicar un término con incógnita por el factor, perdió la incógnita",
    "parentesis_con_mas": "quitó un paréntesis precedido de + cambiando los signos de adentro, como si hubiera un -",
    "factor_doble": "aplicó el factor dos veces a un mismo término",
    "termino_externo": "multiplicó por el factor también un término que estaba fuera del paréntesis",
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


def _productos_anidados(expr):
    """
    Todos los productos 'factor * (suma)' de un lado, a cualquier profundidad (2(3 + 2(x - 1))
    tiene el producto externo y el interno), del más externo al más interno.
    """
    encontrados = []
    for nodo in sp.preorder_traversal(expr):
        if isinstance(nodo, sp.Mul) and any(isinstance(f, sp.Add) for f in _factores(nodo)) and nodo not in encontrados:
            encontrados.append(nodo)
    return encontrados


def _expansiones_erroneas(producto):
    """
    Genera las expansiones erróneas típicas de 'k * (t1 + ... + tn)': en un
    único término tj, el estudiante comete uno de estos errores.
    Devuelve tuplas (tipo_de_error, expansion_erronea, factor_k).
    """
    factores = _factores(producto)
    incognita = next(iter(producto.free_symbols), None)
    sumas = [f for f in factores if isinstance(f, sp.Add)]
    suma = next((f for f in sumas if f.free_symbols), sumas[0])  # (7 - 4)(x + 2): se distribuye (x + 2)
    k = sp.Mul(*[f for f in factores if f is not suma])
    if k.free_symbols:
        return  # (7 - 3)x: el "factor" es la incógnita, no un número que se distribuya
    terminos = [sp.sympify(t).doit() for t in suma.args]  # p. ej. (-1)*4 -> -4

    for j, t in enumerate(terminos):
        def con(nuevo):
            return sp.Add(*[(nuevo if i == j else k * u) for i, u in enumerate(terminos)])

        coef, mono = t.as_coeff_Mul()
        yield "omite_factor", con(t), k # no lo multiplica
        yield "signo", con(-k * t), k # signo equivocado
        yield "factor_doble", con(k * k * t), k # aplica el factor dos veces: 2(3(x - 1) + 5) -> 12(x - 1) + 10
        if not t.free_symbols and incognita is not None:
            yield "agrega_incognita", con(k * t * incognita), k # 5(2x - 3) -> 10x - 15x
        elif t.free_symbols:
            yield "pierde_incognita", con(k * coef), k # 3(4 - x) -> 12 - 3
        if not t.free_symbols and abs(k) != 1:
            # Con un factor 1 o -1 sumar y multiplicar no tienen sentido como confusión: solo es un signo.
            # Sumar en vez de multiplicar solo es un error plausible con los números
            # del paréntesis (2(x + 4) -> 2x + 6), no con el término de la incógnita.
            yield "suma_factor", con(k + t), k                                             # k + t en vez de k * t
            yield "suma_magnitudes", con(sp.sign(k * coef) * (abs(k) + abs(coef)) * mono), k   # |k| + |t|, con el signo de k*t


def _es_parentesis_con_mas(d: Discrepancia):
    """
    Un paréntesis precedido de '+' se quita como si fuera '-': 3x + (x - 7) -> 3x - x + 7.
    Se necesita el texto de S_i porque SymPy elimina ese paréntesis al parsear.
    """
    if not d.texto_i:
        return None
    for m in re.finditer(r"\+\s*\(", d.texto_i):
        texto_erroneo = d.texto_i[:m.start()] + "-" + d.texto_i[m.start() + 1:]
        try:
            izq_w, der_w = parsear_ecuacion(texto_erroneo)
        except Exception:
            continue
        if ecuaciones_equivalentes(izq_w, der_w, d.izq_i_mas_1, d.der_i_mas_1):
            return {
                "regla": "distributiva_incorrecta",
                "variante": "parentesis_con_mas",
                "factor": "1",
                "explicacion": _DESCRIPCION_DISTRIBUTIVA["parentesis_con_mas"],
            }
    return None


def _terminos_de_un_texto(contenido: str):
    """Parte 'a - b + c' (sin mirar dentro de paréntesis) en [(+1, 'a'), (-1, 'b'), (+1, 'c')]."""
    terminos, signo, actual, nivel = [], 1, "", 0
    for ch in contenido:
        if ch in "+-" and nivel == 0:
            if actual.strip():
                terminos.append((signo, actual.strip()))
            signo, actual = (1 if ch == "+" else -1), ""
            continue
        nivel += ch == "("
        nivel -= ch == ")"
        actual += ch
    if actual.strip():
        terminos.append((signo, actual.strip()))
    return terminos


def _es_parentesis_con_menos(d: Discrepancia):
    """
    Un paréntesis precedido de '-' se quita sin cambiar el signo de todos sus términos:
    -(3x - 5) -> -3x - 5 (el 5 debía quedar +5), o x - (2x + 1) -> x - 2x + 1.
    Se prueba, para cada paréntesis con un menos delante, dejar sin cambiar el signo de un término
    (o de todos). Se necesita el texto de S_i porque SymPy distribuye ese menos al parsear.
    """
    if not d.texto_i:
        return None
    texto = d.texto_i
    for m in re.finditer(r"-\s*\(", texto):
        abre = m.end() - 1
        nivel, cierra = 0, None
        for i in range(abre, len(texto)):
            nivel += texto[i] == "("
            nivel -= texto[i] == ")"
            if nivel == 0:
                cierra = i
                break
        if cierra is None:
            continue
        terminos = _terminos_de_un_texto(texto[abre + 1:cierra])
        if not terminos:
            continue
        # j = None: quita el paréntesis sin cambiar ningún signo; j = k: solo el término k conserva su signo
        for j in [None] + list(range(len(terminos))):
            partes = []
            for k, (signo, t) in enumerate(terminos):
                nuevo = signo if (j is None or k == j) else -signo
                partes.append(("+ " if nuevo > 0 else "- ") + t)
            erroneo = texto[:m.start()] + " ".join(partes) + texto[cierra + 1:]
            try:
                izq_w, der_w = parsear_ecuacion(erroneo)
            except Exception:
                continue
            if ecuaciones_equivalentes(izq_w, der_w, d.izq_i, d.der_i):
                continue  # esa lectura no cambia la ecuación: no es un error
            # Se compara lado por lado (no solo por la solución): si el estudiante además pasó términos
            # de un lado al otro, el error puede ser otro (de signo al cambiar de lado).
            if (_forma(izq_w), _forma(der_w)) == (_forma(d.izq_i_mas_1), _forma(d.der_i_mas_1)):
                return {
                    "regla": "distributiva_incorrecta",
                    "variante": "signo",
                    "factor": "-1",
                    "explicacion": _DESCRIPCION_DISTRIBUTIVA["signo"],
                }
    return None


def _es_factor_repetido_afuera(d: Discrepancia):
    """
    Multiplica cada término del paréntesis por el factor, pero deja también el factor afuera:
    3(x + 4) -> 3(3x + 12).
    """
    for nombre, lado, otro in (("izq", d.izq_i, d.der_i), ("der", d.der_i, d.izq_i)):
        for producto in _productos_con_parentesis(lado):
            factores = _factores(producto)
            sumas = [f for f in factores if isinstance(f, sp.Add)]
            if len(sumas) != 1:
                continue
            k = sp.Mul(*[f for f in factores if f is not sumas[0]])
            if k.free_symbols or not k.is_Integer or k in (0, 1, -1):
                continue
            escrito = d.izq_i_mas_1 if nombre == "izq" else d.der_i_mas_1
            if not any(isinstance(f, sp.Add) for p2 in _productos_con_parentesis(escrito) for f in _factores(p2)):
                continue  # el estudiante dejó el factor afuera, o sea, siguió escribiendo un producto con paréntesis
            expansion = k * sp.Add(*[k * sp.sympify(t).doit() for t in sumas[0].args])
            lado_erroneo = lado.xreplace({producto: expansion})
            izq_w, der_w = (lado_erroneo, otro) if nombre == "izq" else (otro, lado_erroneo)
            if ecuaciones_equivalentes(izq_w, der_w, d.izq_i, d.der_i):
                continue
            if ecuaciones_equivalentes(izq_w, der_w, d.izq_i_mas_1, d.der_i_mas_1):
                return {
                    "regla": "distributiva_incorrecta",
                    "variante": "factor_repetido_afuera",
                    "factor": str(k),
                    "explicacion": "multiplicó cada término del paréntesis por el factor, pero lo dejó también afuera",
                }
    return None


def _terminos_en_valor_absoluto(suma):
    """Los términos de una suma sin importar su signo: x - 4 -> {(1, x), (4, 1)}."""
    terminos = Counter()
    for t in sp.Add.make_args(suma):
        coef, resto = t.doit().as_coeff_Mul()  # doit: el parser deja productos como 1*4 sin calcular
        terminos[(abs(sp.nsimplify(coef)), resto)] += 1
    return terminos


def _mismo_producto(q, producto):
    """
    ¿'q' (un producto del paso del estudiante) es el mismo 'factor(suma)' que 'producto'?
    Mismo factor en valor absoluto y, por cada paréntesis de 'producto', un paréntesis de 'q' que
    contiene los mismos términos (salvo el signo, que pudo cambiar al pasar de lado, y términos
    de más: 2(x + 3) -> 2(x + 3 - 3)). Así 3(x + 4) no se confunde con otro 3(x - 2).
    """
    k = abs(sp.Mul(*[f for f in _factores(producto) if not isinstance(f, sp.Add)]))
    kq = abs(sp.Mul(*[f for f in _factores(q) if not isinstance(f, sp.Add)]))
    if sp.simplify(kq - k) != 0:
        return False
    sumas_q = [_terminos_en_valor_absoluto(f) for f in _factores(q) if isinstance(f, sp.Add)]
    for f in _factores(producto):
        if isinstance(f, sp.Add):
            buscados = _terminos_en_valor_absoluto(f)
            if not any(not (buscados - presentes) for presentes in sumas_q):
                return False
    return True


def _sigue_el_producto(escrito, producto):
    """
    ¿Los lados que escribió el estudiante todavía tienen ese mismo producto 'factor(suma)'?
    Si es así, ese paréntesis no se distribuyó en este paso.
    """
    k = abs(sp.Mul(*[f for f in _factores(producto) if not isinstance(f, sp.Add)]))
    if k == 1:
        return False  # un menos delante del paréntesis: quitarlo y dejar otro igual sí puede ser un error de distributiva
    return any(_mismo_producto(q, producto)
               for q in _productos_con_parentesis(escrito[0]) + _productos_con_parentesis(escrito[1]))


def _es_distributiva(d: Discrepancia):
    """Pregunta 1. Devuelve un dict con los detalles si la respuesta es sí; si no, None."""
    respuesta = _es_parentesis_con_mas(d) or _es_parentesis_con_menos(d) or _es_factor_repetido_afuera(d)
    if respuesta:
        return respuesta
    for nombre, lado, otro in (("izq", d.izq_i, d.der_i), ("der", d.der_i, d.izq_i)):
        escrito = (d.izq_i_mas_1, d.der_i_mas_1)  # el producto pudo haber cambiado de lado
        for producto in _productos_anidados(lado):
            if _sigue_el_producto(escrito, producto):
                continue  # el estudiante sigue con el paréntesis y el mismo factor: aún no distribuyó
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
        # (a + b)(x + c): distribuye solo un término del primer paréntesis y deja suelto el otro
        for producto in _productos_con_parentesis(lado):
            sumas = [f for f in _factores(producto) if isinstance(f, sp.Add)]
            if len(sumas) != 2 or len(_factores(producto)) != 2:
                continue
            for i_a, i_b in ((0, 1), (1, 0)):
                A, B = sumas[i_a], sumas[i_b]
                terminos_a = [sp.sympify(t).doit() for t in A.args]
                for j, ta in enumerate(terminos_a):
                    expansion = sp.Add(*[(ta * B if i == j else u) for i, u in enumerate(terminos_a)])
                    lado_erroneo = lado.xreplace({producto: expansion})
                    izq_w, der_w = (lado_erroneo, otro) if nombre == "izq" else (otro, lado_erroneo)
                    if ecuaciones_equivalentes(izq_w, der_w, d.izq_i, d.der_i):
                        continue
                    if ecuaciones_equivalentes(izq_w, der_w, d.izq_i_mas_1, d.der_i_mas_1):
                        return {
                            "regla": "distributiva_incorrecta",
                            "variante": "un_termino_del_factor",
                            "factor": str(B),
                            "explicacion": "multiplicó el paréntesis solo por uno de los términos del otro paréntesis",
                        }
        # el factor también se aplica a un término que está fuera del paréntesis: 4(x + 2) - 3 -> 4x + 8 - 12
        if isinstance(lado, sp.Add):
            for producto in _productos_con_parentesis(lado):
                if producto not in lado.args:
                    continue
                factores = _factores(producto)
                k = sp.Mul(*[f for f in factores if not isinstance(f, sp.Add)])
                for u in lado.args:
                    if u == producto:
                        continue
                    lado_erroneo = lado.xreplace({u: k * u})
                    izq_w, der_w = (lado_erroneo, otro) if nombre == "izq" else (otro, lado_erroneo)
                    if ecuaciones_equivalentes(izq_w, der_w, d.izq_i, d.der_i):
                        continue
                    if ecuaciones_equivalentes(izq_w, der_w, d.izq_i_mas_1, d.der_i_mas_1):
                        return {
                            "regla": "distributiva_incorrecta",
                            "variante": "termino_externo",
                            "factor": str(k),
                            "explicacion": _DESCRIPCION_DISTRIBUTIVA["termino_externo"],
                        }
    return None


# --------------------------------------------------------------------------
# OPERACIÓN EN UN SOLO LADO
# --------------------------------------------------------------------------
def _lado_intacto(antes, despues):
    """¿Un lado de la ecuación quedó igual (como valor) en el paso del estudiante?"""
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
    if any(n.is_Float for lado in (d.izq_i, d.der_i) for n in sp.preorder_traversal(lado)):
        multiplicadores = multiplicadores | {10, 100}  # quitar los decimales multiplicando por 10 o 100
    divisores = set()
    for lado in (d.izq_i, d.der_i):
        for t in _terminos(lado):
            coef, mono = t.as_coeff_Mul()
            coef = abs(sp.nsimplify(coef))
            if mono.free_symbols and coef.is_Rational and coef.p != 1:
                divisores.add(int(coef.p))
    # también con signo negativo: multiplicar o dividir por -2 solo en un lado (para dejar la x positiva)
    multiplicadores = multiplicadores | {-c for c in multiplicadores}
    divisores = divisores | {-c for c in divisores}

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
        return None  # los dos lados cambiaron: no se puede hablar de "un solo lado"

    calculo = _es_aritmetica(d)
    es_calculo = bool(calculo and calculo["multiplicador"] == "1")  # simplificación con un número mal calculado

    for descripcion, nombre, multiplicador, tipo, izq_w, der_w in _hipotesis_un_lado(d):
        if nombre != lado_operado:
            continue  # la operación solo puede estar en el lado que el estudiante modificó
        if multiplicador in (10, 100) and es_calculo:
            continue  # x = 7.2/3 -> x = 24 es un cálculo mal hecho, no "multiplicó por 10 en un lado"
        if tipo in ("suma_resta", "divide") and es_calculo:
            # Cambiar un lado en +3 puede coincidir numéricamente con "sumar 3 en un solo lado",
            # pero si el lado tenía algo por calcular es un error de cálculo (pregunta 3).
            continue
        if ecuaciones_equivalentes(izq_w, der_w, d.izq_i, d.der_i):
            continue  # la "operación" no cambia la ecuación: no es un error
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
    """Un lado de la ecuación como {monomio: coeficiente}, con los términos ya combinados y evaluados."""
    expr = sp.expand(sp.sympify(lado).doit())
    forma = {}
    for t in sp.Add.make_args(expr):
        coef, mono = t.as_coeff_Mul()
        forma[mono] = forma.get(mono, 0) + sp.nsimplify(coef)
    return {m: c for m, c in forma.items() if c != 0}


def _tiene_algo_por_calcular(lado):
    """
    ¿El lado, tal como está escrito, todavía se puede simplificar (sumar, combinar
    términos semejantes, evaluar una fracción o un paréntesis)? '15 + 3 - 6', '6x - 4x'
    o '18/6' sí; '11', '2x + 3' o '5/2' no.
    """
    terminos = sp.Add.make_args(lado)
    if len(terminos) > len(_forma(lado)):  # hay términos que se pueden combinar
        return True
    for t in terminos:
        factores = _factores(t)
        if any(isinstance(f, sp.Add) for f in factores):  # una suma dentro de un paréntesis o fracción
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
            continue  # ese lado quedó igual: no lo multiplicó, y eso no es un error de cálculo
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
    divisores = [f for f in factores if isinstance(f, sp.Pow) and f.exp == -1 and not f.base.free_symbols]
    if len(divisores) != 1:
        return None
    resto = [f for f in factores if f is not divisores[0]]
    if sp.nsimplify(sp.Mul(*resto)) != sp.nsimplify(numerador):  # 7.5 y 15/2 son el mismo número
        return None
    return divisores[0].base


def _es_division(d: Discrepancia):
    """
    El paso anterior es 'a x = b' (o 'b = a x'; a distinto de 0 y de 1, b un número) y el
    estudiante despeja escribiendo 'x = b / d' (o 'b / d = x') con un divisor d que no es a.
    El coeficiente puede ser entero, decimal o una fracción como 3x/5. El divisor puede ser un
    número o una fracción (6/(5/3)). El divisor tiene que estar escrito en el paso: si solo
    aparece el resultado no se puede saber por cuánto dividió.
    """
    for izq, der in ((d.izq_i, d.der_i), (d.der_i, d.izq_i)):
        forma_izq, forma_der = _forma(izq), _forma(der)
        incognitas = [m for m in forma_izq if m != 1]
        if len(incognitas) != 1 or len(forma_izq) != 1 or not set(forma_der) <= {1}:
            continue
        x = incognitas[0]
        a, b = forma_izq[x], forma_der.get(1, 0)
        escrito_decimal = any(n.is_Float for n in sp.preorder_traversal(izq))
        if not escrito_decimal and not (a.is_Integer or (a.is_Rational and a.p != 1)):
            # Con x/2 = 11 -> x = 11/2 el estudiante multiplica un lado y divide el otro: no es
            # "dividir entre un número equivocado". Se deja como indeterminado, igual que en el benchmark.
            continue
        if a == 1:
            continue
        for izq_n, der_n in ((d.izq_i_mas_1, d.der_i_mas_1), (d.der_i_mas_1, d.izq_i_mas_1)):
            if _forma(izq_n) != {x: 1}:
                continue
            divisor = _division_escrita(der_n, b)
            if divisor is None or sp.simplify(sp.nsimplify(sp.sympify(divisor).doit()) - sp.nsimplify(a)) == 0:
                continue
            if not a.is_Integer and not escrito_decimal and sp.nsimplify(sp.sympify(divisor).doit()).is_Integer:
                # (2/3)x = 6 -> x = 6/2: con un coeficiente fraccionario, dividir entre un entero es
                # mezclar numerador y denominador, no "dividir entre un número equivocado" (indeterminado).
                continue
            return {
                "regla": "division_coeficiente_equivocado",
                "coeficiente": str(a),
                "divisor_usado": str(divisor),
                "explicacion": f"dividió entre {divisor} en vez de dividir entre el coeficiente {a}",
            }
    return _es_division_con_parentesis(d)


def _es_division_entre_un_termino_del_coeficiente(d: Discrepancia):
    """
    El coeficiente está escrito como una suma, '(5 - 2)x = 12', y el estudiante divide solo entre
    uno de sus términos y deja el otro sumando: 'x = 12/5 - 2' en vez de 'x = 12/(5 - 2)'.
    """
    for izq, der, izq_n, der_n in (
        (d.izq_i, d.der_i, d.izq_i_mas_1, d.der_i_mas_1),
        (d.der_i, d.izq_i, d.der_i_mas_1, d.izq_i_mas_1),
    ):
        factores = _factores(izq) if isinstance(izq, sp.Mul) else []
        sumas = [f for f in factores if isinstance(f, sp.Add) and not f.free_symbols]
        resto = [f for f in factores if not (isinstance(f, sp.Add) and not f.free_symbols)]
        if len(sumas) != 1 or len(resto) != 1 or not resto[0].is_Symbol or set(_forma(der)) - {1}:
            continue
        if sp.simplify(izq_n - resto[0]) != 0:
            continue
        b = _forma(der).get(1, 0)
        terminos = [sp.sympify(t).doit() for t in sumas[0].args]
        for j, t in enumerate(terminos):
            if t == 0:
                continue
            erroneo = b / t + sum(u for i, u in enumerate(terminos) if i != j)
            if sp.simplify(der_n - erroneo) == 0 and sp.simplify(erroneo - b / sumas[0]) != 0:
                return {
                    "regla": "division_coeficiente_equivocado",
                    "coeficiente": str(sumas[0]),
                    "divisor_usado": str(t),
                    "explicacion": f"el coeficiente es {sumas[0]}, pero dividió solo entre {t}",
                }
    return None


def _es_division_con_parentesis(d: Discrepancia):
    """
    'k(expresión) = b' -> 'expresión = b / m' con m distinto de k: para quitar el factor del
    paréntesis divide entre un número que no es ese factor (3(2x - 1) = 15 -> 2x - 1 = 15/2).
    """
    for izq, der, izq_n, der_n in (
        (d.izq_i, d.der_i, d.izq_i_mas_1, d.der_i_mas_1),
        (d.der_i, d.izq_i, d.der_i_mas_1, d.izq_i_mas_1),
    ):
        if not isinstance(izq, sp.Mul) or not _forma(der) or set(_forma(der)) - {1}:
            continue
        factores = _factores(izq)
        sumas = [f for f in factores if isinstance(f, sp.Add)]
        if len(sumas) != 1:
            continue
        k = sp.Mul(*[f for f in factores if f is not sumas[0]])
        if not k.is_Integer or k in (0, 1, -1) or sp.simplify(izq_n - sumas[0]) != 0:
            continue
        b = _forma(der).get(1, 0)
        divisor = _division_escrita(der_n, b)
        if divisor is None or sp.nsimplify(divisor) == k:
            continue
        return {
            "regla": "division_coeficiente_equivocado",
            "coeficiente": str(k),
            "divisor_usado": str(divisor),
            "explicacion": f"para quitar el factor {k} dividió entre {divisor}",
        }
    return _es_division_entre_un_termino_del_coeficiente(d)


# --------------------------------------------------------------------------
# ERROR DE SIGNO
# --------------------------------------------------------------------------
def _es_signo(d: Discrepancia):
    """
    Hipótesis: un término t pasó al otro lado de la igualdad SIN cambiarle el
    signo (en vez de restarlo en ambos lados, lo sumó en el otro). Se usan los
    términos tal como están escritos en S_i. Solo se contempla UN término mal;
    dos errores de signo en el mismo paso quedan como indeterminado.
    """
    opuesta = _es_operacion_con_signo_opuesto(d)
    if opuesta:
        return opuesta
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
    return _es_signo_dentro_de_lo_que_pasa(d)


def _es_operacion_con_signo_opuesto(d: Discrepancia):
    """
    Mira la ecuación tal como se escribió (sin simplificar): el estudiante dejó cada lado
    como estaba y le agregó el mismo término con signo opuesto en cada lado:
    2x + 7 = 15 -> 2x + 7 - 7 = 15 + 7. SymPy simplifica "2x + 7 - 7" y pierde esa pista.
    """
    if "=" not in d.texto_i or "=" not in d.texto_i_mas_1:
        return None
    li, ri = (x.replace(" ", "") for x in d.texto_i.split("=", 1))
    le, re_ = (x.replace(" ", "") for x in d.texto_i_mas_1.split("=", 1))
    if not (le.startswith(li) and re_.startswith(ri)):
        return None
    m_izq = re.fullmatch(r"([+-])\s*(.+)", le[len(li):].strip())
    m_der = re.fullmatch(r"([+-])\s*(.+)", re_[len(ri):].strip())
    if not (m_izq and m_der):
        return None
    if m_izq.group(2).strip() != m_der.group(2).strip() or m_izq.group(1) == m_der.group(1):
        return None
    t = m_izq.group(2).strip()
    op_i = "restó" if m_izq.group(1) == "-" else "sumó"
    op_d = "restó" if m_der.group(1) == "-" else "sumó"
    return {
        "regla": "error_signo",
        "termino": t,
        "explicacion": f"a la izquierda {op_i} {t} pero a la derecha {op_d} {t}: la operación tiene signo opuesto en cada lado",
    }


def _es_signo_dentro_de_lo_que_pasa(d: Discrepancia):
    """
    Pasa al otro lado un término con paréntesis (o una fracción con suma en el numerador) y,
    además de cambiarle el signo al término, le cambia por error el signo a algo de adentro:
    x/2 - (x - 4)/3 = 1 -> x/2 = 1 + (x + 4)/3.
    """
    for nombre, lado, otro in (("izq", d.izq_i, d.der_i), ("der", d.der_i, d.izq_i)):
        for t in sp.Add.make_args(lado):
            sumas = [f for f in _factores(t) if isinstance(f, sp.Add)]
            if len(sumas) != 1:
                continue
            interior = list(sumas[0].args)
            for j in range(len(interior)):
                nuevo = sp.Add(*[(-u if i == j else u) for i, u in enumerate(interior)])
                t_mal = t.xreplace({sumas[0]: nuevo})
                lado_w, otro_w = lado - t, otro - t_mal
                izq_w, der_w = (lado_w, otro_w) if nombre == "izq" else (otro_w, lado_w)
                if ecuaciones_equivalentes(izq_w, der_w, d.izq_i, d.der_i):
                    continue
                if ecuaciones_equivalentes(izq_w, der_w, d.izq_i_mas_1, d.der_i_mas_1):
                    return {
                        "regla": "error_signo",
                        "termino": str(t),
                        "explicacion": f"pasó {t} al otro lado y además le cambió el signo a un término de adentro",
                    }
    return None


# --------------------------------------------------------------------------
# Errores fuera de la taxonomía que se reconocen para dar una explicación propia
# --------------------------------------------------------------------------
def _denominador_escrito(termino):
    """Si el término trae un '/n' con n un número entero, devuelve n; si no, None."""
    for f in _factores(termino):
        if isinstance(f, sp.Pow) and f.exp == -1 and f.base.is_Integer and f.base > 1:
            return int(f.base)
    return None


def _es_division_de_toda_la_suma(d: Discrepancia):
    """
    Lee '6 + 4x/2' como '(6 + 4x)/2': la división solo era del último término y la aplica a toda la suma.
    """
    for nombre, lado, otro in (("izq", d.izq_i, d.der_i), ("der", d.der_i, d.izq_i)):
        terminos = list(sp.Add.make_args(lado))
        if len(terminos) < 2:
            continue
        for j, t in enumerate(terminos):
            c = _denominador_escrito(t)
            if c is None or not t.free_symbols:
                continue  # 3 - 1/4 con números solos es un cálculo; esta lectura es la de 6 + 4x/2
            erroneo = sp.Add(*[(u * c if i == j else u) for i, u in enumerate(terminos)]) / c
            izq_w, der_w = (erroneo, otro) if nombre == "izq" else (otro, erroneo)
            if ecuaciones_equivalentes(izq_w, der_w, d.izq_i, d.der_i):
                continue
            if ecuaciones_equivalentes(izq_w, der_w, d.izq_i_mas_1, d.der_i_mas_1):
                return {
                    "regla": "orden_de_operaciones",
                    "explicacion": f"dividió entre {c} toda la suma, y la división era solo de un término",
                }
    return None


def _es_orden_de_operaciones(d: Discrepancia):
    """
    Hace la suma o la resta antes de la multiplicación: 8 - 3(x - 2) -> (8 - 3)(x - 2), o
    x - 4*2 -> (x - 4)*2. Se prueba, para cada término u y cada producto p = k*m de un mismo
    lado, la lectura equivocada (u + k)*m.
    """
    if _es_division_de_toda_la_suma(d):
        return _es_division_de_toda_la_suma(d)
    for nombre, lado, otro in (("izq", d.izq_i, d.der_i), ("der", d.der_i, d.izq_i)):
        if not isinstance(lado, sp.Add):
            continue
        for p in lado.args:
            factores = _factores(p)
            if not isinstance(p, sp.Mul) or len([f for f in factores if f != -1]) < 2:
                continue  # el signo menos solo no es un producto: -x o -4 no son "k por m"
            for i, m in enumerate(factores):
                if m == -1 or not (m.is_Number or isinstance(m, sp.Add)):
                    continue  # el factor que se multiplica por la suma es un número o un paréntesis
                k = sp.Mul(*[f for j, f in enumerate(factores) if j != i])
                if k.free_symbols or k == 0:
                    continue
                for u in lado.args:
                    if u == p:
                        continue
                    resto = [a for a in lado.args if a is not u and a is not p]
                    erroneo = sp.Add(*resto, (u + k) * m)
                    izq_w, der_w = (erroneo, otro) if nombre == "izq" else (otro, erroneo)
                    if ecuaciones_equivalentes(izq_w, der_w, d.izq_i, d.der_i):
                        continue
                    if ecuaciones_equivalentes(izq_w, der_w, d.izq_i_mas_1, d.der_i_mas_1):
                        return {
                            "regla": "orden_de_operaciones",
                            "explicacion": "hizo la suma o la resta antes de la multiplicación",
                        }
    return None


def _es_factor_comun_mal_sacado(d: Discrepancia):
    """
    Saca factor común sin dividir un término: 4x + 8 -> 4(x + 8). El lado nuevo es k(suma) y, al
    expandirlo, difiere del lado anterior en un solo término, multiplicado por k. El otro lado no cambia.
    """
    for antes, despues, otro_a, otro_d in (
        (d.izq_i, d.izq_i_mas_1, d.der_i, d.der_i_mas_1),
        (d.der_i, d.der_i_mas_1, d.izq_i, d.izq_i_mas_1),
    ):
        factores = _factores(despues) if isinstance(despues, sp.Mul) else []
        sumas = [f for f in factores if isinstance(f, sp.Add)]
        if len(sumas) != 1 or not _lado_intacto(otro_a, otro_d):
            continue
        k = sp.Mul(*[f for f in factores if f is not sumas[0]])
        if not k.is_Integer or k in (0, 1, -1):
            continue
        if _productos_anidados(antes):
            continue  # el lado ya tenía un paréntesis con factor: no sacó un factor común, aplicó mal una distributiva
        fa, fd = _forma(antes), _forma(despues)
        if set(fa) != set(fd):
            continue
        distintos = [m for m in fa if fa[m] != fd[m]]
        if len(distintos) == 1 and fd[distintos[0]] == k * fa[distintos[0]]:
            return {
                "regla": "factor_comun_mal_sacado",
                "factor": str(k),
                "explicacion": f"sacó el factor común {k} sin dividir uno de los términos entre {k}",
            }
    return None


def _es_cada_fraccion_por_su_denominador(d: Discrepancia):
    """
    Para quitar denominadores distintos se multiplica todo por el mínimo común múltiplo L. El
    estudiante multiplica cada fracción u/n por su propio denominador n en lugar de por L/n:
    (x + 1)/2 + x/3 = 4 -> 2(x + 1) + 3x = 24 (debía ser 3(x + 1) + 2x = 24).
    """
    terminos_i = list(sp.Add.make_args(d.izq_i)), list(sp.Add.make_args(d.der_i))
    denominadores = {n for lado in terminos_i for t in lado for n in [_denominador_escrito(t)] if n}
    if len(denominadores) < 2:
        return None
    L = int(sp.ilcm(*denominadores))
    lados = []
    for lado in terminos_i:
        # u/n -> n*u (el numerador por su propio denominador); un término sin fracción se multiplica por L
        lados.append(sp.Add(*[t * (_denominador_escrito(t) ** 2 if _denominador_escrito(t) else L) for t in lado]))
    # la parte derecha puede no tener fracciones: se multiplica por L; si las tiene, se trata igual
    correcto = (_forma(L * d.izq_i), _forma(L * d.der_i))
    hipotesis = (_forma(lados[0]), _forma(lados[1]))
    if hipotesis == correcto:
        return None  # con estos denominadores multiplicar por el propio o por L/n da lo mismo: no hay error
    # se compara término a término (no solo por la solución), para no confundirlo con otro error
    if hipotesis == (_forma(d.izq_i_mas_1), _forma(d.der_i_mas_1)):
        return {
            "regla": "cada_fraccion_por_su_denominador",
            "explicacion": "para quitar los denominadores multiplicó cada fracción por su propio denominador en vez de por el mínimo común múltiplo",
        }
    return None


def _es_cada_lado_por_su_denominador(d: Discrepancia):
    """
    Ambos lados traen una fracción con denominadores distintos y el estudiante multiplica cada lado
    por SU PROPIO denominador: 3x/2 = (x + 5)/4 -> 3x = x + 5. Son dos operaciones distintas (una por
    lado), no un cálculo mal hecho. Se lee el denominador tal como está escrito (2x/6 -> 6).
    """
    if "=" not in d.texto_i:
        return None
    lado_i, lado_d = (x.strip() for x in d.texto_i.split("=", 1))
    m_i = re.search(r"/\s*(\d+)\s*$", lado_i)
    m_d = re.search(r"/\s*(\d+)\s*$", lado_d)
    if not (m_i and m_d):
        return None
    b, c = int(m_i.group(1)), int(m_d.group(1))
    if b == c or b < 2 or c < 2:
        return None
    if sp.simplify(d.izq_i_mas_1 - b * d.izq_i) == 0 and sp.simplify(d.der_i_mas_1 - c * d.der_i) == 0:
        return {
            "regla": "cada_lado_por_su_denominador",
            "explicacion": f"multiplicó el lado izquierdo por {b} y el derecho por {c}, cada uno por su propio denominador",
        }
    return None


# --------------------------------------------------------------------------
# Limpieza de los textos de la explicación
# --------------------------------------------------------------------------
def _limpiar_texto(texto: str):
    """
    Deja los números como los escribiría una persona. El parser deja productos como '1*4' sin calcular
    ('x - 1*4') y SymPy imprime decimales largos ('0.200000000000000'); eso no se le puede mostrar a un
    estudiante ni citar en una pista.
    """
    def decimal_largo(m):
        f = Fraction(m.group(0)).limit_denominator(1000)
        if abs(float(f) - float(m.group(0))) > 1e-9:
            return m.group(0)  # no es una fracción sencilla: se deja el decimal tal cual
        return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"

    texto = re.sub(r"\d+\.\d{6,}", decimal_largo, texto)
    return re.sub(r"(?<![\w.])1\*(?=[\w(])", "", texto)


# --------------------------------------------------------------------------
# Punto de entrada
# --------------------------------------------------------------------------
def _diagnosticar_sin_limpiar(discrepancia: Discrepancia) -> ResultadoDiagnostico:
    """
    Punto de entrada del módulo de diagnóstico. Recibe la discrepancia
    reportada por el verificador (ver src/verificador/verificador.py) y
    devuelve la categoría de error correspondiente según la taxonomía.

    Los detalles solo contienen texto, para que se puedan devolver tal cual
    por la API y usar luego en la generación de la retroalimentación.
    """
    detalles = {"diferencia": discrepancia.diferencia}

    # Errores que la taxonomía no tiene como categoría: se reconocen primero para que no se
    # confundan con otra categoría, pero se informan como "indeterminado" con su explicación.
    for detector in (_es_orden_de_operaciones, _es_factor_comun_mal_sacado, _es_cada_lado_por_su_denominador,
                     _es_cada_fraccion_por_su_denominador):
        respuesta = detector(discrepancia)
        if respuesta:
            return ResultadoDiagnostico("indeterminado", {**detalles, **respuesta})

    # 1. ¿Falla en un término distribuido?
    respuesta = _es_distributiva(discrepancia)
    if respuesta:
        return ResultadoDiagnostico("distributiva_incorrecta", {**detalles, **respuesta})

    # 2. ¿Se operó solo en un lado?
    respuesta = _es_un_lado(discrepancia)
    if respuesta:
        return ResultadoDiagnostico("operacion_un_lado", {**detalles, **respuesta})

    # 3a. Despeje: ¿dividió entre un número que no es el coeficiente?
    respuesta = _es_division(discrepancia)
    if respuesta:
        return ResultadoDiagnostico("division_coeficiente_equivocado", {**detalles, **respuesta})

    # 3. ¿Operación bien, cálculo mal?
    respuesta = _es_aritmetica(discrepancia)
    if respuesta and respuesta["multiplicador"] != "1" and sp.nsimplify(respuesta["valor_escrito"]) == -sp.nsimplify(respuesta["valor_correcto"]):
        # al multiplicar los dos lados para quitar denominadores, un número cambió solo de signo
        return ResultadoDiagnostico("error_signo", {**detalles, **respuesta, "regla": "error_signo",
                                    "explicacion": f"al multiplicar por {respuesta['multiplicador']}, el número {respuesta['valor_correcto']} perdió su signo"})
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


def obtener_categoria(categoria_id: str):
    """Devuelve la información completa de una categoría a partir de su id."""
    for categoria in TAXONOMIA["categorias"]:
        if categoria["id"] == categoria_id:
            return categoria
    raise ValueError(f"Categoría desconocida: {categoria_id}")


def diagnosticar(discrepancia: Discrepancia) -> ResultadoDiagnostico:
    """Ejecuta el diagnóstico y limpia los textos de los detalles antes de devolverlos."""
    resultado = _diagnosticar_sin_limpiar(discrepancia)
    detalles = {k: (_limpiar_texto(v) if isinstance(v, str) else v) for k, v in resultado.detalles.items()}
    return ResultadoDiagnostico(resultado.categoria_id, detalles)
