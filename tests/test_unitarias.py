from datetime import date
import pytest
from validador import ValidadorDeAvistamiento


class RelojFijo:
    """Stub artesanal para la interfaz Reloj que devuelve una fecha fija (2026-10-21)."""

    def __init__(self, fecha_fija: date = date(2026, 10, 21)) -> None:
        self._fecha = fecha_fija

    def hoy(self) -> date:
        return self._fecha


@pytest.fixture
def reloj_stub():
    return RelojFijo(date(2026, 10, 21))


@pytest.fixture
def validador(reloj_stub):
    return ValidadorDeAvistamiento(reloj=reloj_stub)


# ==============================================================================
# CICLO 1: Campo especie - Límite inferior inválido (2 caracteres)
# ==============================================================================

def test_rechaza_especie_de_2_caracteres_indicando_el_campo_especie(validador):
    # Arrange
    datos = {
        "especie": "ab",
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-21",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert len(errores) > 0
    assert any(e["campo"] == "especie" for e in errores)


def test_acepta_especie_de_3_caracteres_limite_inferior_valido(validador):
    # Arrange
    datos = {
        "especie": "ave",
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-21",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert not any(e["campo"] == "especie" for e in errores)


# ==============================================================================
# CICLO 2: Campo especie - Límite superior inválido (51 caracteres)
# ==============================================================================

def test_rechaza_especie_de_51_caracteres_limite_superior_invalido(validador):
    # Arrange
    datos = {
        "especie": "a" * 51,
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-21",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert len(errores) > 0
    assert any(e["campo"] == "especie" for e in errores)


def test_acepta_especie_de_50_caracteres_limite_superior_valido(validador):
    # Arrange
    datos = {
        "especie": "a" * 50,
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-21",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert not any(e["campo"] == "especie" for e in errores)


def test_rechaza_especie_con_espacios_de_longitud_efectiva_2(validador):
    # Arrange
    datos = {
        "especie": "  ab  ",
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-21",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert len(errores) > 0
    assert any(e["campo"] == "especie" for e in errores)


@pytest.mark.parametrize("especie_invalida", ["", "   ", None, 123])
def test_rechaza_especie_vacia_espacios_nula_o_tipo_invalido(validador, especie_invalida):
    # Arrange
    datos = {
        "especie": especie_invalida,
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-21",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert len(errores) > 0
    assert any(e["campo"] == "especie" for e in errores)


# ==============================================================================
# CICLO 3: Campo fecha - Límite superior inválido (mañana: 2026-10-22)
# ==============================================================================

def test_rechaza_fecha_posterior_a_hoy_limite_manana_indicando_campo_fecha(validador):
    # Arrange
    datos = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-22",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert len(errores) > 0
    assert any(e["campo"] == "fecha" for e in errores)


def test_acepta_fecha_de_hoy_limite_superior_valido(validador):
    # Arrange
    datos = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-21",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert not any(e["campo"] == "fecha" for e in errores)


def test_acepta_fecha_de_ayer_limite_valido(validador):
    # Arrange
    datos = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-20",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert not any(e["campo"] == "fecha" for e in errores)


def test_acepta_fecha_bisiesto_pasada_valida(validador):
    # Arrange
    datos = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": "2024-02-29",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert not any(e["campo"] == "fecha" for e in errores)


def test_rechaza_fecha_bisiesto_invalida_en_ano_comun(validador):
    # Arrange
    datos = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": "2026-02-29",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert len(errores) > 0
    assert any(e["campo"] == "fecha" for e in errores)


@pytest.mark.parametrize("fecha_invalida", [
    "2026-02-30",
    "2026-13-45",
    "21/10/2026",
    "2026-10-21 ",
    "",
    "   ",
    None,
])
def test_rechaza_fecha_con_formato_imposible_espacios_o_nula(validador, fecha_invalida):
    # Arrange
    datos = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": fecha_invalida,
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert len(errores) > 0
    assert any(e["campo"] == "fecha" for e in errores)


# ==============================================================================
# CICLO 4: Campo lugar - No vacío
# ==============================================================================

@pytest.mark.parametrize("lugar_invalido", ["", "   ", None, 123])
def test_rechaza_lugar_vacio_espacios_o_nulo(validador, lugar_invalido):
    # Arrange
    datos = {
        "especie": "colibrí",
        "lugar": lugar_invalido,
        "fecha": "2026-10-21",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert len(errores) > 0
    assert any(e["campo"] == "lugar" for e in errores)


def test_acepta_lugar_y_observador_validos_limite_un_caracter(validador):
    # Arrange
    datos = {
        "especie": "ave",
        "lugar": "A",
        "fecha": "2026-10-21",
        "observador": "O"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert errores == []


# ==============================================================================
# CICLO 5: Campo observador - No vacío
# ==============================================================================

@pytest.mark.parametrize("observador_invalido", ["", "   ", None, 456])
def test_rechaza_observador_vacio_espacios_o_nulo(validador, observador_invalido):
    # Arrange
    datos = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-21",
        "observador": observador_invalido
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert len(errores) > 0
    assert any(e["campo"] == "observador" for e in errores)


def test_acepta_avistamiento_completamente_valido_representativo(validador):
    # Arrange
    datos = {
        "especie": "Colibrí coliazul",
        "lugar": "Jardín Botánico - Sendero A",
        "fecha": "2026-10-21",
        "observador": "Carlos Ruiz"
    }

    # Act
    errores = validador.validar(datos)

    # Assert
    assert errores == []


# ==============================================================================
# CICLO 6: Dobles de prueba en el Servicio (Fake y Mock)
# ==============================================================================

class RepositorioEnMemoria:
    """
    Doble de prueba tipo FAKE:
    Implementación funcional y simplificada en memoria (sin SQLite ni I/O).
    """

    def __init__(self) -> None:
        self.registros: list[dict] = []
        self._next_id: int = 1

    def listar(self) -> list[dict]:
        return list(self.registros)

    def obtener_por_id(self, id: int):
        for item in self.registros:
            if item["id"] == id:
                return item
        return None

    def crear(self, datos: dict) -> dict:
        nuevo = {"id": self._next_id, **datos}
        self.registros.append(nuevo)
        self._next_id += 1
        return nuevo

    def actualizar(self, id: int, datos: dict):
        for i, item in enumerate(self.registros):
            if item["id"] == id:
                actualizado = {"id": id, **datos}
                self.registros[i] = actualizado
                return actualizado
        return None

    def eliminar(self, id: int) -> bool:
        inicial = len(self.registros)
        self.registros = [r for r in self.registros if r["id"] != id]
        return len(self.registros) < inicial

    def resumen_por_especie(self) -> dict[str, int]:
        resumen = {}
        for r in self.registros:
            esp = r["especie"]
            resumen[esp] = resumen.get(esp, 0) + 1
        return resumen


def test_servicio_crea_y_lista_avistamientos_con_repositorio_fake(validador):
    # Arrange
    from servicio import ServicioAvistamientos
    repo_fake = RepositorioEnMemoria()
    servicio = ServicioAvistamientos(repositorio=repo_fake, validador=validador)
    datos = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-21",
        "observador": "Carlos Ruiz"
    }

    # Act
    creado = servicio.crear(datos)
    todos = servicio.listar_todos()

    # Assert (Verificación de estado con FAKE)
    assert creado["id"] == 1
    assert creado["especie"] == "colibrí"
    assert len(todos) == 1
    assert todos[0] == creado


def test_servicio_no_invoca_repositorio_crear_cuando_datos_son_invalidos_mock(validador):
    # Arrange
    from unittest.mock import Mock
    from servicio import ServicioAvistamientos
    from repositorio import RepositorioAvistamientos

    repo_mock = Mock(spec=RepositorioAvistamientos)
    servicio = ServicioAvistamientos(repositorio=repo_mock, validador=validador)
    datos_invalidos = {
        "especie": "ab",  # Límite inválido: 2 caracteres
        "lugar": "Jardín Botánico",
        "fecha": "2026-10-21",
        "observador": "Carlos Ruiz"
    }

    # Act
    with pytest.raises(ValueError) as exc_info:
        servicio.crear(datos_invalidos)

    # Assert (Verificación de comportamiento con MOCK)
    assert "especie" in str(exc_info.value)
    repo_mock.crear.assert_not_called()


def test_validador_rechaza_cuerpo_no_diccionario(validador):
    # Arrange
    datos_no_dict = ["colibrí", "Jardín"]

    # Act
    errores = validador.validar(datos_no_dict)

    # Assert
    assert len(errores) > 0
    assert errores[0]["campo"] == "cuerpo"
    assert "objeto JSON" in errores[0]["mensaje"]
