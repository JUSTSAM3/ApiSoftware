from datetime import date
from typing import Protocol


class Reloj(Protocol):
    """Interfaz (abstracción) para obtener la fecha actual."""
    def hoy(self) -> date:
        ...


class RelojSistema:
    """Implementación real de Reloj basada en el reloj del sistema operativo."""
    def hoy(self) -> date:
        return date.today()
