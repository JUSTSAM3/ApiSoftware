import sqlite3
from pathlib import Path
from flask import g, current_app

# Ruta por defecto para la base de datos en el mismo directorio del proyecto
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "avistamientos.db"


def get_db():
    """
    Obtiene la conexión a la base de datos para la petición HTTP actual.
    Se almacena en el objeto 'g' de Flask para reutilizarla durante la misma petición.
    """
    if "db" not in g:
        # Obtenemos la ruta configurada en la aplicación (útil para pruebas con base temporal)
        db_path = current_app.config.get("DATABASE", DEFAULT_DB_PATH)
        g.db = sqlite3.connect(str(db_path))
        # sqlite3.Row permite acceder a las columnas por nombre (ej. fila['especie'])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """
    Cierra la conexión a la base de datos al finalizar la petición HTTP.
    Flask invoca esta función automáticamente gracias a teardown_appcontext.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(db_path=None):
    """
    Crea el archivo de base de datos y la tabla 'avistamientos' si aún no existen.
    Se ejecuta al iniciar la aplicación sin necesidad de scripts externos.
    """
    ruta = Path(db_path) if db_path else DEFAULT_DB_PATH
    
    # Aseguramos que la carpeta contenedora exista (especialmente en pruebas temporales)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(ruta))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS avistamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            especie TEXT NOT NULL,
            lugar TEXT NOT NULL,
            fecha TEXT NOT NULL,
            observador TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
