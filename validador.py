from datetime import datetime
from typing import Any, Dict, List
from reloj import Reloj


class ValidadorDeAvistamiento:
    """
    Validador de reglas de negocio para avistamientos.
    Inyecta una abstracción Reloj por constructor para desacoplar el tiempo del sistema (DIP).
    """

    def __init__(self, reloj: Reloj) -> None:
        self.reloj = reloj

    def validar(self, datos: Any) -> List[Dict[str, str]]:
        """Valida los datos de un avistamiento según las reglas de negocio."""
        errores = []
        if not isinstance(datos, dict):
            return [{"campo": "cuerpo", "mensaje": "El cuerpo debe ser un objeto JSON válido."}]

        # 1. Validación de especie (entre 3 y 50 caracteres inclusive)
        especie = datos.get("especie")
        if not isinstance(especie, str) or not (3 <= len(especie.strip()) <= 50):
            errores.append({
                "campo": "especie",
                "mensaje": "El campo 'especie' debe tener entre 3 y 50 caracteres."
            })

        # 2. Validación de fecha (AAAA-MM-DD, fecha real, no posterior a hoy)
        fecha_str = datos.get("fecha")
        error_fecha = self._validar_fecha(fecha_str)
        if error_fecha:
            errores.append({"campo": "fecha", "mensaje": error_fecha})

        # 3. Validación de lugar (no vacío)
        lugar = datos.get("lugar")
        if not isinstance(lugar, str) or not lugar.strip():
            errores.append({
                "campo": "lugar",
                "mensaje": "El campo 'lugar' no puede estar vacío."
            })

        # 4. Validación de observador (no vacío)
        observador = datos.get("observador")
        if not isinstance(observador, str) or not observador.strip():
            errores.append({
                "campo": "observador",
                "mensaje": "El campo 'observador' no puede estar vacío."
            })

        return errores

    def _validar_fecha(self, fecha_str: Any) -> str | None:
        if not isinstance(fecha_str, str):
            return "El campo 'fecha' debe ser una cadena de texto en formato AAAA-MM-DD."

        partes = fecha_str.split("-")
        if len(partes) != 3 or len(partes[0]) != 4 or len(partes[1]) != 2 or len(partes[2]) != 2:
            return "El campo 'fecha' debe cumplir exactamente el formato AAAA-MM-DD y ser una fecha válida."

        try:
            fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return "El campo 'fecha' debe cumplir exactamente el formato AAAA-MM-DD y ser una fecha válida."

        if fecha_dt > self.reloj.hoy():
            return "El campo 'fecha' no puede ser posterior a hoy."

        return None
