from typing import Any, Dict, List, Optional
from repositorio import RepositorioAvistamientos
from validador import ValidadorDeAvistamiento


class ServicioAvistamientos:
    """
    Capa de servicio que orquesta la lógica de negocio y persistencia de avistamientos.
    Aplica Inversión de Dependencias (DIP) al depender de abstracciones inyectadas por constructor.
    """

    def __init__(
        self,
        repositorio: RepositorioAvistamientos,
        validador: Optional[ValidadorDeAvistamiento] = None,
    ) -> None:
        self.repositorio = repositorio
        self.validador = validador

    def listar_todos(self) -> List[Dict[str, Any]]:
        return self.repositorio.listar()

    def obtener_por_id(self, id: int) -> Optional[Dict[str, Any]]:
        return self.repositorio.obtener_por_id(id)

    def crear(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        if self.validador:
            errores = self.validador.validar(datos)
            if errores:
                raise ValueError(errores[0]["mensaje"])
        return self.repositorio.crear(datos)

    def actualizar(self, id: int, datos: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.validador:
            errores = self.validador.validar(datos)
            if errores:
                raise ValueError(errores[0]["mensaje"])
        return self.repositorio.actualizar(id, datos)

    def eliminar(self, id: int) -> bool:
        return self.repositorio.eliminar(id)

    def obtener_resumen(self) -> Dict[str, int]:
        return self.repositorio.resumen_por_especie()
