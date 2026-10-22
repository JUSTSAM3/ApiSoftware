from typing import Any, Dict, List, Optional, Protocol
import sqlite3
from database import get_db


class RepositorioAvistamientos(Protocol):
    """Interfaz (abstracción) para el almacenamiento y consulta de avistamientos."""

    def listar(self) -> List[Dict[str, Any]]:
        ...

    def obtener_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        ...

    def crear(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def actualizar(self, id: int, datos: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ...

    def eliminar(self, id: int) -> bool:
        ...

    def resumen_por_especie(self) -> Dict[str, int]:
        ...


class RepositorioAvistamientosSQLite:
    """Implementación de RepositorioAvistamientos sobre la base de datos embebida SQLite."""

    def __init__(self, db_getter=get_db) -> None:
        self._get_db = db_getter

    @property
    def db(self) -> sqlite3.Connection:
        return self._get_db()

    def listar(self) -> List[Dict[str, Any]]:
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT id, especie, lugar, fecha, observador FROM avistamientos ORDER BY id ASC"
        )
        return [dict(fila) for fila in cursor.fetchall()]

    def obtener_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT id, especie, lugar, fecha, observador FROM avistamientos WHERE id = ?",
            (id,),
        )
        fila = cursor.fetchone()
        return dict(fila) if fila else None

    def crear(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT INTO avistamientos (especie, lugar, fecha, observador)
            VALUES (?, ?, ?, ?)
            """,
            (
                datos["especie"],
                datos["lugar"],
                datos["fecha"],
                datos["observador"],
            ),
        )
        self.db.commit()
        nuevo_id = cursor.lastrowid
        return {"id": nuevo_id, **datos}

    def actualizar(self, id: int, datos: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        cursor = self.db.cursor()
        cursor.execute("SELECT id FROM avistamientos WHERE id = ?", (id,))
        if cursor.fetchone() is None:
            return None

        cursor.execute(
            """
            UPDATE avistamientos
            SET especie = ?, lugar = ?, fecha = ?, observador = ?
            WHERE id = ?
            """,
            (
                datos["especie"],
                datos["lugar"],
                datos["fecha"],
                datos["observador"],
                id,
            ),
        )
        self.db.commit()
        return {"id": id, **datos}

    def eliminar(self, id: int) -> bool:
        cursor = self.db.cursor()
        cursor.execute("SELECT id FROM avistamientos WHERE id = ?", (id,))
        if cursor.fetchone() is None:
            return False

        cursor.execute("DELETE FROM avistamientos WHERE id = ?", (id,))
        self.db.commit()
        return True

    def resumen_por_especie(self) -> Dict[str, int]:
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT especie, COUNT(*) AS cantidad
            FROM avistamientos
            GROUP BY especie
            ORDER BY cantidad DESC
            """
        )
        return {fila["especie"]: fila["cantidad"] for fila in cursor.fetchall()}
