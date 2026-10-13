from pathlib import Path
from flask import Flask, jsonify
from database import DEFAULT_DB_PATH, init_db, close_db
from routes import bp


def create_app(db_path=None):
    """
    Fábrica de aplicaciones (Application Factory pattern).
    Permite instanciar la app configurando una ruta de base de datos específica,
    lo cual facilita enormemente la ejecución de pruebas con bases de datos temporales.
    """
    app = Flask(__name__)

    # Configuración de la ruta de la base de datos
    ruta_db = Path(db_path) if db_path else DEFAULT_DB_PATH
    app.config["DATABASE"] = ruta_db

    # Aseguramos la existencia de la tabla en SQLite al arrancar
    init_db(ruta_db)

    # Registro de la función de limpieza de conexiones al terminar cada petición
    app.teardown_appcontext(close_db)

    # Registro del blueprint con los endpoints de avistamientos
    app.register_blueprint(bp)

    # --- Manejadores de errores globales en formato JSON ---
    @app.errorhandler(400)
    def handle_bad_request(error):
        return jsonify({"error": "Petición inválida o cuerpo JSON mal formado."}), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({"error": "Recurso o ruta no encontrada."}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify({"error": "Método HTTP no permitido para esta ruta."}), 405

    @app.errorhandler(500)
    def handle_internal_error(error):
        return jsonify({"error": "Error interno del servidor."}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    # Ejecuta el servidor en http://127.0.0.1:5000
    print("Iniciando servidor API de Avistamientos en http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
