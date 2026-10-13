from datetime import datetime
from flask import Blueprint, request, jsonify
from database import get_db

bp = Blueprint("avistamientos", __name__)

CAMPOS_REQUERIDOS = ["especie", "lugar", "fecha", "observador"]


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
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, especie, lugar, fecha, observador FROM avistamientos ORDER BY id ASC")
    filas = cursor.fetchall()
    
    # Convertimos cada fila de sqlite3.Row a diccionario de Python
    resultado = [dict(fila) for fila in filas]
    return jsonify(resultado), 200


@bp.route("/avistamientos/resumen", methods=["GET"])
def resumen_avistamientos():
    """
    Retorna la cantidad de avistamientos agrupados por especie.
    Ejemplo de respuesta: {"colibrí": 3, "águila": 1}
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT especie, COUNT(*) AS cantidad
        FROM avistamientos
        GROUP BY especie
        ORDER BY cantidad DESC
    """)
    filas = cursor.fetchall()
    
    # Creamos un diccionario asociando especie -> cantidad
    resumen = {fila["especie"]: fila["cantidad"] for fila in filas}
    return jsonify(resumen), 200


@bp.route("/avistamientos/<int:id>", methods=["GET"])
def obtener_avistamiento(id):
    """Obtiene el detalle de un avistamiento específico por su ID."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, especie, lugar, fecha, observador FROM avistamientos WHERE id = ?", (id,))
    fila = cursor.fetchone()
    
    if fila is None:
        return jsonify({"error": f"No se encontró el avistamiento con id {id}."}), 404

    return jsonify(dict(fila)), 200


@bp.route("/avistamientos", methods=["POST"])
def crear_avistamiento():
    """Registra un nuevo avistamiento de ave."""
    # silent=True evita excepciones internas de Flask si el cuerpo no es JSON válido
    datos = request.get_json(silent=True)
    datos_validados, error = validar_datos_avistamiento(datos)
    if error:
        return jsonify({"error": error}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO avistamientos (especie, lugar, fecha, observador)
        VALUES (?, ?, ?, ?)
        """,
        (
            datos_validados["especie"],
            datos_validados["lugar"],
            datos_validados["fecha"],
            datos_validados["observador"]
        )
    )
    db.commit()

    nuevo_id = cursor.lastrowid
    nuevo_avistamiento = {
        "id": nuevo_id,
        **datos_validados
    }
    return jsonify(nuevo_avistamiento), 201


@bp.route("/avistamientos/<int:id>", methods=["PUT"])
def actualizar_avistamiento(id):
    """Actualiza por completo los datos de un avistamiento existente."""
    db = get_db()
    cursor = db.cursor()

    # Verificamos si el recurso a actualizar existe en la base de datos
    cursor.execute("SELECT id FROM avistamientos WHERE id = ?", (id,))
    if cursor.fetchone() is None:
        return jsonify({"error": f"No se encontró el avistamiento con id {id}."}), 404

    # Validamos los nuevos datos enviados en el cuerpo
    datos = request.get_json(silent=True)
    datos_validados, error = validar_datos_avistamiento(datos)
    if error:
        return jsonify({"error": error}), 400

    cursor.execute(
        """
        UPDATE avistamientos
        SET especie = ?, lugar = ?, fecha = ?, observador = ?
        WHERE id = ?
        """,
        (
            datos_validados["especie"],
            datos_validados["lugar"],
            datos_validados["fecha"],
            datos_validados["observador"],
            id
        )
    )
    db.commit()

    avistamiento_actualizado = {
        "id": id,
        **datos_validados
    }
    return jsonify(avistamiento_actualizado), 200


@bp.route("/avistamientos/<int:id>", methods=["DELETE"])
def eliminar_avistamiento(id):
    """Elimina un avistamiento por su ID."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT id FROM avistamientos WHERE id = ?", (id,))
    if cursor.fetchone() is None:
        return jsonify({"error": f"No se encontró el avistamiento con id {id}."}), 404

    cursor.execute("DELETE FROM avistamientos WHERE id = ?", (id,))
    db.commit()

    # La respuesta 204 No Content se envía sin cuerpo
    return "", 204
