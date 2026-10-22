from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from database import get_db

bp = Blueprint("avistamientos", __name__)

CAMPOS_REQUERIDOS = ["especie", "lugar", "fecha", "observador"]


def get_servicio():
    """Obtiene el servicio configurado en la aplicación Flask o crea uno por defecto."""
    if current_app:
        servicio = current_app.config.get("SERVICIO")
        if servicio is not None:
            return servicio
    from repositorio import RepositorioAvistamientosSQLite
    from servicio import ServicioAvistamientos
    from validador import ValidadorDeAvistamiento
    from reloj import RelojSistema

    return ServicioAvistamientos(
        repositorio=RepositorioAvistamientosSQLite(),
        validador=ValidadorDeAvistamiento(reloj=RelojSistema()),
    )


def validar_fecha(fecha_str):
    """
    Verifica que la fecha cumpla exactamente el formato AAAA-MM-DD
    y corresponda a una fecha real del calendario (ej. rechaza '2026-13-45' o '2026-02-30').
    """
    if not isinstance(fecha_str, str):
        return False
    
    partes = fecha_str.split("-")
    if len(partes) != 3 or len(partes[0]) != 4 or len(partes[1]) != 2 or len(partes[2]) != 2:
        return False

    try:
        datetime.strptime(fecha_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validar_datos_avistamiento(data):
    """
    Valida el cuerpo JSON para las operaciones POST y PUT.
    Retorna una tupla: (datos_limpios, None) si todo es correcto,
    o (None, mensaje_error) si no cumple las reglas de negocio.
    """
    if not isinstance(data, dict):
        return None, "El cuerpo de la petición debe ser un objeto JSON válido."

    for campo in CAMPOS_REQUERIDOS:
        if campo not in data:
            return None, f"El campo '{campo}' es obligatorio."
        valor = data[campo]
        if not isinstance(valor, str):
            return None, f"El campo '{campo}' debe ser una cadena de texto."
        if not valor.strip():
            return None, f"El campo '{campo}' no puede estar vacío ni contener solo espacios en blanco."

    if not validar_fecha(data["fecha"]):
        return None, "El campo 'fecha' debe cumplir exactamente el formato AAAA-MM-DD y ser una fecha válida."

    # Extraemos solo los campos requeridos y limpiamos espacios alrededor
    # De esta manera, si el cliente envía un campo 'id', este es completamente ignorado
    datos_limpios = {
        "especie": data["especie"].strip(),
        "lugar": data["lugar"].strip(),
        "fecha": data["fecha"].strip(),
        "observador": data["observador"].strip()
    }
    return datos_limpios, None


@bp.route("/avistamientos", methods=["GET"])
def listar_avistamientos():
    """Lista todos los avistamientos registrados ordenados por id."""
    servicio = get_servicio()
    resultado = servicio.listar_todos()
    return jsonify(resultado), 200


@bp.route("/avistamientos/resumen", methods=["GET"])
def resumen_avistamientos():
    """
    Retorna la cantidad de avistamientos agrupados por especie.
    Ejemplo de respuesta: {"colibrí": 3, "águila": 1}
    """
    servicio = get_servicio()
    resumen = servicio.obtener_resumen()
    return jsonify(resumen), 200


@bp.route("/avistamientos/<int:id>", methods=["GET"])
def obtener_avistamiento(id):
    """Obtiene el detalle de un avistamiento específico por su ID."""
    servicio = get_servicio()
    item = servicio.obtener_por_id(id)
    if item is None:
        return jsonify({"error": f"No se encontró el avistamiento con id {id}."}), 404

    return jsonify(item), 200


@bp.route("/avistamientos", methods=["POST"])
def crear_avistamiento():
    """Registra un nuevo avistamiento de ave."""
    # silent=True evita excepciones internas de Flask si el cuerpo no es JSON válido
    datos = request.get_json(silent=True)
    datos_validados, error = validar_datos_avistamiento(datos)
    if error:
        return jsonify({"error": error}), 400

    servicio = get_servicio()
    if servicio.validador:
        errores_negocio = servicio.validador.validar(datos_validados)
        if errores_negocio:
            primer_error = errores_negocio[0]
            mensaje = primer_error.get(
                "mensaje", f"El campo '{primer_error.get('campo')}' es inválido."
            )
            return jsonify({"error": mensaje}), 400

    nuevo_avistamiento = servicio.crear(datos_validados)
    return jsonify(nuevo_avistamiento), 201


@bp.route("/avistamientos/<int:id>", methods=["PUT"])
def actualizar_avistamiento(id):
    """Actualiza por completo los datos de un avistamiento existente."""
    servicio = get_servicio()

    # Verificamos si el recurso a actualizar existe en la base de datos
    if servicio.obtener_por_id(id) is None:
        return jsonify({"error": f"No se encontró el avistamiento con id {id}."}), 404

    # Validamos los nuevos datos enviados en el cuerpo
    datos = request.get_json(silent=True)
    datos_validados, error = validar_datos_avistamiento(datos)
    if error:
        return jsonify({"error": error}), 400

    if servicio.validador:
        errores_negocio = servicio.validador.validar(datos_validados)
        if errores_negocio:
            primer_error = errores_negocio[0]
            mensaje = primer_error.get(
                "mensaje", f"El campo '{primer_error.get('campo')}' es inválido."
            )
            return jsonify({"error": mensaje}), 400

    avistamiento_actualizado = servicio.actualizar(id, datos_validados)
    return jsonify(avistamiento_actualizado), 200


@bp.route("/avistamientos/<int:id>", methods=["DELETE"])
def eliminar_avistamiento(id):
    """Elimina un avistamiento por su ID."""
    servicio = get_servicio()
    eliminado = servicio.eliminar(id)
    if not eliminado:
        return jsonify({"error": f"No se encontró el avistamiento con id {id}."}), 404

    # La respuesta 204 No Content se envía sin cuerpo
    return "", 204
