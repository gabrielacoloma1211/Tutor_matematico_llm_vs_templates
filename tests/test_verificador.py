"""
Pruebas del verificador matemático, usando los mismos ejemplos definidos en
la taxonomía de errores del proyecto.
"""
import pytest

from src.verificador.verificador import verificar_paso, parsear_ecuacion, ErrorDeParseo


class TestPasosValidos:
    def test_transposicion_correcta(self):
        r = verificar_paso("6*x - 4 = 3", "6*x = 3 + 4")
        assert r.valido is True
        assert r.discrepancia is None

    def test_distributiva_correcta(self):
        r = verificar_paso("3*(x - 4) = 12", "3*x - 12 = 12")
        assert r.valido is True

    def test_multiplicar_ambos_lados(self):
        # multiplicar toda la ecuación por una constante no debe cambiar su validez
        r = verificar_paso("x + 5 = 12", "2*x + 10 = 24")
        assert r.valido is True

    def test_reordenar_lados(self):
        r = verificar_paso("x + 5 = 12", "12 = x + 5")
        assert r.valido is True


class TestErroresDeSigno:
    def test_signo_no_invertido_al_transponer(self):
        # Ejemplo de la taxonomía: error de signo.
        r = verificar_paso("6*x - 4 = 3", "6*x = 3 - 4")
        assert r.valido is False
        assert r.discrepancia is not None


class TestErroresDistributiva:
    def test_distributiva_incompleta(self):
        # Ejemplo de la taxonomía: no multiplica el -4 por 3.
        r = verificar_paso("3*(x - 4) = 12", "3*x - 4 = 12")
        assert r.valido is False


class TestErroresUnLado:
    def test_operacion_solo_en_un_lado(self):
        # Ejemplo de la taxonomía: restó 5 solo del lado izquierdo.
        r = verificar_paso("x + 5 = 12", "x = 12")
        assert r.valido is False


class TestErroresAritmeticos:
    def test_simplificacion_aritmetica_incorrecta(self):
        # Ejemplo de la taxonomía: 10 - 3 = 7, no 6.
        r = verificar_paso("2*x = 10 - 3", "2*x = 6")
        assert r.valido is False


class TestErroresDivision:
    def test_division_por_coeficiente_equivocado(self):
        # Ejemplo de la taxonomía: dividió por 4, no por 5.
        r = verificar_paso("5*x = 20", "x = 5")
        assert r.valido is False


class TestParseo:
    def test_ecuacion_sin_signo_igual_lanza_error(self):
        with pytest.raises(ErrorDeParseo):
            parsear_ecuacion("6*x - 4")

    def test_ecuacion_con_dos_signos_igual_lanza_error(self):
        with pytest.raises(ErrorDeParseo):
            parsear_ecuacion("6*x = 4 = 2")
