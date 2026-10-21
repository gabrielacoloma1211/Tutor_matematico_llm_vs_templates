"""
Validación de seguridad de las ecuaciones.

Antes de usar parse_expr de SymPy, se revisa que la ecuación sea segura.
Esto es necesario porque parse_expr puede interpretar texto como código Python.

La función validar_ecuacion revisa el texto sin usar SymPy ni eval.

Solo permite:
- Números, decimales, x, operaciones (+, -, *, /), paréntesis y un solo =.
- Multiplicación implícita, como 3x o 2(x + 1).
- Signos negativos, como -x o 3 - -2, pero no --x.
- Ecuaciones de primer grado (no permite x*x, x/x ni dividir entre expresiones con x).

También establece límites para evitar entradas demasiado grandes:
- Máximo 100 caracteres y 60 símbolos.
- Máximo 5 niveles de paréntesis.
- Máximo 9 dígitos por número.

Esta validación se aplica a todas las ecuaciones, sin importar si vienen
de la API, del benchmark o de las pruebas.
"""
import re

MAX_LONGITUD = 100
MAX_SIMBOLOS = 60
MAX_PROFUNDIDAD = 5
MAX_DIGITOS = 9

_TOKEN = re.compile(r"[ ]*(?:(?P<num>[0-9]+(?:\.[0-9]+)?)|(?P<x>x)|(?P<op>[-+*/])|(?P<par>[()]))")


class EntradaNoPermitida(Exception):
    """
    La ecuación no se puede procesar. `tipo` distingue dos casos:
      - "error_de_formato": está mal escrita (por ejemplo "3x + = 7", falta un paréntesis);
      - "entrada_no_permitida": está bien escrita, pero usa algo que el proyecto no admite
        (letras o funciones, otros operadores, potencias, ecuaciones de grado mayor que 1,
        entradas demasiado largas).
    """

    def __init__(self, mensaje, tipo="entrada_no_permitida"):
        super().__init__(mensaje)
        self.tipo = tipo


def _formato(mensaje):
    return EntradaNoPermitida(mensaje, tipo="error_de_formato")


def _tokens(texto):
    pos, out = 0, []
    texto = texto.rstrip(" ")
    while pos < len(texto):
        m = _TOKEN.match(texto, pos)
        if not m or m.end() == pos:
            malo = texto[pos:].lstrip(" ")[:1]
            raise EntradaNoPermitida(f"el carácter o texto '{malo}' no está permitido; "
                                     "solo se admiten dígitos, x, + - * / ( ) . y =")
        kind = m.lastgroup
        val = m.group(kind)
        if kind == "num":
            if len(val.replace(".", "")) > MAX_DIGITOS:
                raise EntradaNoPermitida(f"el número '{val[:12]}' es demasiado largo (máximo {MAX_DIGITOS} dígitos)")
        out.append((kind, val))
        pos = m.end()
        if len(out) > MAX_SIMBOLOS:
            raise EntradaNoPermitida(f"la expresión es demasiado larga (máximo {MAX_SIMBOLOS} símbolos)")
    return out


class _Analizador:
    """expr := term (('+'|'-') term)* ; term := factor (('*'|'/')? factor)* ; factor := [+|-] atomo."""

    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def _ver(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def _es(self, kind, val=None):
        k, v = self._ver()
        return k == kind and (val is None or v == val)

    def expresion(self, profundidad):
        if profundidad > MAX_PROFUNDIDAD:
            raise EntradaNoPermitida(f"demasiados paréntesis anidados (máximo {MAX_PROFUNDIDAD})")
        grado = self.termino(profundidad)
        while self._es("op") and self._ver()[1] in "+-":
            self.i += 1
            grado = max(grado, self.termino(profundidad))
        return grado

    def termino(self, profundidad):
        grado = self.factor(profundidad)
        while True:
            k, v = self._ver()
            if k == "op" and v in "*/":
                self.i += 1
                if v == "*":
                    grado += self.factor(profundidad)
                else:
                    if self.factor(profundidad) != 0:
                        raise EntradaNoPermitida("no se puede dividir entre una expresión con x")
            elif k in ("x", "par") and (k == "x" or v == "("):
                grado += self.factor(profundidad)          # multiplicación implícita: 3x, 3(x - 4), x(x + 1)
            else:
                return grado

    def factor(self, profundidad):
        if self._es("op") and self._ver()[1] in "+-":
            self.i += 1
            if self._es("op") and self._ver()[1] in "+-":
                raise _formato("hay dos signos seguidos (por ejemplo '--')")
        k, v = self._ver()
        if k == "num":
            self.i += 1
            if self._es("num"):
                raise _formato("hay dos números seguidos sin operador")
            return 0
        if k == "x":
            self.i += 1
            return 1
        if k == "par" and v == "(":
            self.i += 1
            if self._es("par", ")"):
                raise _formato("hay un paréntesis vacío")
            grado = self.expresion(profundidad + 1)
            if not self._es("par", ")"):
                raise _formato("falta cerrar un paréntesis")
            self.i += 1
            return grado
        if k is None:
            raise _formato("la expresión está incompleta (falta un número, una x o un paréntesis)")
        raise _formato(f"se esperaba un número, una x o un paréntesis y se encontró '{v}'")


def validar_expresion(texto):
    """Valida un lado de la ecuación. Devuelve su grado en x (0 o 1)."""
    tokens = _tokens(texto)
    if not tokens:
        raise _formato("falta una expresión a un lado del signo =")
    a = _Analizador(tokens)
    grado = a.expresion(1)
    if a.i != len(tokens):
        k, v = a._ver()
        if k == "par" and v == ")":
            raise _formato("hay un paréntesis de cierre sin su apertura")
        raise _formato(f"no se esperaba '{v}' en esa posición")
    if grado > 1:
        raise EntradaNoPermitida("solo se admiten ecuaciones de primer grado (la x no puede multiplicarse por sí misma)")
    return grado


def validar_ecuacion(texto):
    """Valida una ecuación completa. Lanza EntradaNoPermitida si no se admite."""
    if not isinstance(texto, str):
        raise EntradaNoPermitida("la ecuación debe ser un texto")
    if len(texto) > MAX_LONGITUD:
        raise EntradaNoPermitida(f"la ecuación es demasiado larga (máximo {MAX_LONGITUD} caracteres)")
    if "=" not in texto:
        raise _formato("la ecuación no contiene un signo '='")
    lados = texto.split("=")
    if len(lados) != 2:
        raise _formato("la ecuación debe tener exactamente un '='")
    for lado in lados:
        validar_expresion(lado)
