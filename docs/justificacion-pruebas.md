# Justificación de pruebas: API de avistamientos de aves

- **Autor:** Samuel Andres Mesa Comaz  
- **Fecha:** 21 de octubre de 2026 (Sesión 22, ISW-2)  
- **Lenguaje y framework:** Python 3.14.6 · Flask 3.1.3 · pytest 9.1.1  
- **Herramienta de IA y modelo:** Gemini 3.8 Flash (en IDE Antigravity)  

---

## 1. Qué cambió en el código

### Contrato original de la API (Sesión 17, 29 de septiembre)
El servicio gestiona el recurso **avistamiento** (`id`, `especie`, `lugar`, `fecha`, `observador`) mediante seis operaciones HTTP preservadas intactas:
- `GET /avistamientos`: 200 OK con la lista completa JSON ordenada por ID.
- `GET /avistamientos/<id>`: 200 OK con el registro o 404 Not Found si no existe.
- `POST /avistamientos`: 201 Created con el nuevo objeto o 400 Bad Request si faltan campos o son inválidos.
- `PUT /avistamientos/<id>`: 200 OK con el objeto mutado, 404 si el ID no existe o 400 si los datos son inválidos.
- `DELETE /avistamientos/<id>`: 204 No Content si se elimina o 404 si no existe.
- `GET /avistamientos/resumen`: 200 OK con el conteo agrupado por especie.

### Refactor arquitectónico e Inversión de Dependencias (DIP)
Para posibilitar pruebas unitarias independientes sin alterar los contratos existentes, se aplicó **Inversión de Dependencias (DIP)** mediante cuatro extracciones:
1. **Abstracción del Reloj (`reloj.py`):** Interfaz `Reloj` (`Protocol`, `hoy() -> date`) y su implementación `RelojSistema` (`date.today()`).
2. **Validador independiente (`validador.py`):** `ValidadorDeAvistamiento`, desacoplado de Flask y SQLite. Recibe `Reloj` por constructor (DIP) y retorna errores estructurados `[{'campo': ..., 'mensaje': ...}]`.
3. **Capa de Repositorio (`repositorio.py`):** Contrato `RepositorioAvistamientos` (`Protocol`) e implementación `RepositorioAvistamientosSQLite`.
4. **Capa de Servicio (`servicio.py`):** `ServicioAvistamientos`, que valida antes de delegar la persistencia en el repositorio.
5. **Inyección en controladores (`routes.py` y `app.py`):** `create_app` inyecta dependencias en `app.config` y permite aislar SQLite en `tmp_path`.

### Impacto en la testabilidad
- **Controlabilidad:** Permite fijar estados arbitrariamente. Con `Reloj`, se congela la fecha actual mediante un **Stub**, garantizando pruebas repetibles en cualquier fecha (**FIRST: Repetible**). Con `RepositorioAvistamientos`, se sustituye SQLite por un **Fake** en memoria.
- **Observabilidad:** El validador devuelve errores estructurados `{'campo': ..., 'mensaje': ...}`, permitiendo inspeccionar la causa exacta de fallo a nivel de unidad sin depender de serializaciones HTTP ni excepciones opacas.
- **Inversión de Dependencias (DIP):** Los módulos de dominio dependen de abstracciones (`Reloj`, `RepositorioAvistamientos`), permitiendo intercambiar dependencias por dobles en tiempo de ejecución.

---

## 2. Tabla de casos de la Parte A

Se aplicaron dos técnicas sistemáticas de caja negra de la Sesión 20: **partición de equivalencia** (división del dominio en clases válidas e inválidas) y **análisis de valores límite** (evaluación de fronteras exactas y adyacentes, donde se concentra la mayor densidad de fallas).

### Decisiones de frontera y negocio
1. **Espacios en especie:** Se evalúa tras `strip()`. `"  ab  "` cuenta como **2 caracteres** y es **inválido (400)**. Evita burlar la longitud mínima con espacios espurios y mantiene la persistencia limpia.
2. **Calendario real y bisiestos:** Formato estricto `AAAA-MM-DD`. `2024-02-29` es **válido** (bisiesto real pasado respecto a hoy `2026-10-21`); `2026-02-29` es **inválido** (año común); `2028-02-29` es **inválido** (bisiesto futuro).

### Casos de prueba canónicos (Límites obligatorios, Fecha base: `2026-10-21`)

| Campo | Límite / Partición | Valor | Esperado | Justificación técnica |
|---|---|---|:---:|---|
| `especie` | Límite $-1$ ($n=2$) | `"ab"` | 400 | Longitud insuficiente |
| `especie` | Límite exacto ($n=3$) | `"ave"` | 200/201 | Frontera mínima válida permitida |
| `especie` | Representativo ($n=7$) | `"colibrí"` | 200/201 | Longitud válida en rango $[3, 50]$ |
| `especie` | Límite exacto ($n=50$) | `"a"*50` | 200/201 | Frontera máxima válida permitida |
| `especie` | Límite $+1$ ($n=51$) | `"a"*51` | 400 | Longitud excedida |
| `fecha` | Hoy (límite superior) | `"2026-10-21"` | 200/201 | Fecha actual permitida |
| `fecha` | Mañana (límite $+1$) | `"2026-10-22"` | 400 | Fecha futura prohibida |
| `lugar` | Cadena vacía | `""` | 400 | Campo obligatorio no vacío |
| `observador`| Cadena vacía | `""` | 400 | Campo obligatorio no vacío |

*(El catálogo exhaustivo de los 35 casos con cadenas vacías, bisiestos y tipos de datos se encuentra documentado en el Anexo A.2).*

### Metodología TDD y pruebas nacidas en verde
Se siguió el ciclo **Rojo $\rightarrow$ Verde $\rightarrow$ Refactor** (las tres reglas de Martin):
1. Las pruebas de rechazo (`especie` de 2 car, 51 car, `fecha` de mañana, `lugar` vacío) nacieron en **rojo** antes de escribir código de producción.
2. Algunas pruebas de casos válidos (ej. `especie` de 3 caracteres) nacieron en **verde** debido a que el esqueleto inicial devolvía lista vacía. Una prueba en verde adquiere valor probatorio al combinarse con su contraparte inválida (`"ab"`), formando el par de valores límite que acota la frontera.

---

## 3. Por qué cada nivel

El plan de pruebas evalúa las responsabilidades según la **Pirámide de Pruebas** (Cohn, 2009) y el **Panal de Microservicios** (Spotify, 2018):

### Nivel Unitario vs. Nivel de Integración

1. **`test_rechaza_especie_de_2_caracteres` (Unitaria):**
   - *Propósito:* Verifica la lógica pura del `ValidadorDeAvistamiento` en memoria (0.001s), sin Flask, red ni base de datos.
   - *Límite:* No detecta si el controlador mapea el error a `400 Bad Request`, si el JSON es válido o si Flask aborta con 500.
2. **`test_post_rechaza_especie_corta_regla_nueva` (Integración):**
   - *Propósito:* Envía JSON real mediante `test_client`, atraviesa middleware, enrutador, validación y verifica efectos colaterales en SQLite.
   - *Qué detecta que la unitaria no puede:* Serialización `Content-Type: application/json`, código HTTP 400 y que no hubo `INSERT` en SQLite (la tabla permanece vacía).
3. **`test_crear_avistamiento_exitoso` (Integración):**
   - Comprueba la colaboración completa: deserialización JSON $\rightarrow$ validación $\rightarrow$ traducción a sentencia SQL `INSERT` $\rightarrow$ autoincremento de ID $\rightarrow$ `commit()` de transacción $\rightarrow$ respuesta `201 Created`. Ninguna prueba con dobles puede verificar la sintaxis SQL ni el dialecto de SQLite.

### Ubicación del proyecto: El Panal de Pruebas (Spotify)
Dado que es una API REST enfocada en persistencia CRUD, la suite adopta forma de **Panal**:
- **Base unitaria focalizada (34 pruebas):** Validación pura de negocio y orquestación del servicio.
- **Cuerpo robusto de integración (25 pruebas):** Mayor peso de la suite, pues el principal riesgo en microservicios radica en la **frontera tecnológica**: dialecto SQL, transacciones, códigos HTTP y serialización JSON.

---

## 4. Los dobles

Se implementaron tres tipos de dobles con justificaciones basadas en Meszaros (2007) y Fowler (2007):

| Doble | Tipo | Dependencia | Criterio de elección (Por qué este tipo) |
|---|:---:|---|---|
| `RelojFijo` | **Stub** | `Reloj` (`RelojSistema`) | **Verificación de estado:** Proporciona fecha fija e invariable (`2026-10-21`) para comprobar el estado resultante de la validación. |
| `RepositorioEnMemoria` | **Fake** | `RepositorioAvistamientos` (`SQLite`) | **Implementación funcional simplificada:** Lista en memoria que simula persistencia sin I/O de disco, permitiendo probar el servicio ultrarrápidamente. |
| `repo_mock` | **Mock** | `RepositorioAvistamientos` | **Verificación de comportamiento:** En la regla *"si los datos son inválidos, el repositorio NUNCA se llama a guardar"*, verifica que `crear` no fue invocado (`assert_not_called`). |

### ¿Qué habría pasado sin los dobles?
- Sin el Stub `RelojFijo`, la prueba de "fecha de mañana" pasaría hoy y fallaría catastróficamente al día siguiente, destruyendo la propiedad **FIRST: Repetible**.
- Sin el Fake ni el Mock, las pruebas del servicio dependerían de SQLite en disco, haciéndose lentas y propensas a contaminación entre ejecuciones.

### Riesgo de que el doble se equivoque y su comprobación
Un doble es una simplificación:
- El Fake no valida restricciones relacionales ni tipos `NOT NULL` de SQLite. Comprobación: `test_crear_avistamiento_exitoso` ejecuta SQL real en SQLite y verifica inserción y claves.
- El Stub asume fecha congelada. Comprobación: `test_post_rechaza_fecha_futura_regla_nueva` valida que el endpoint completo rechaza fechas futuras en integración.

---

## 5. Lo que no probamos

Decidir no probar algo es una decisión técnica consciente basada en riesgo, costo y beneficio:

1. **Pruebas de concurrencia y carga masiva de base de datos:**  
   *Justificación:* Principio 2 de ISTQB: *Las pruebas exhaustivas son imposibles*. Según el Principio 4 (*Los defectos se agrupan*), el riesgo principal en una API académica radica en validación y mapeo, no en la concurrencia de SQLite.
2. **El punto de entrada manual `if __name__ == '__main__': app.run(...)` (`app.py:66-69`):**  
   *Justificación:* Código de arranque terminal. En pruebas se usa `create_app()` con `test_client`, haciendo innecesario y riesgoso levantar sockets reales de red.
3. **Manejadores globales de error 500 (`handle_internal_error`) y 400 (`handle_bad_request`):**  
   *Justificación:* En `TESTING = True`, Flask propaga excepciones a pytest para depuración. Forzar pruebas simuladas violaría la **Ley de Goodhart**, subiendo la cobertura sin probar lógica de dominio.
4. **Implementación de producción `RelojSistema.hoy()` (`reloj.py:14`):**  
   *Justificación:* Delegación de una línea a `datetime.date.today()`, probada por el fabricante de Python. Probarla violaría la repetibilidad (**FIRST**).

---

## 6. Lectura de la cobertura

Se midió la cobertura con `pytest-cov` sobre la suite completa (59 pruebas: 34 unitarias y 25 de integración).

### Criterios medidos y resultados cuantitativos

1. **Cobertura de sentencias (*Statement Coverage*):** Porcentaje de líneas ejecutables transitadas por las pruebas.
2. **Cobertura de ramas (*Branch Coverage*):** Porcentaje de caminos booleanos (`True`/`False`) evaluados en cada condicional.

| Módulo | Sentencias (*Stmts*) | Ramas (*Branch*) | Cobertura | Líneas no cubiertas |
|---|:---:|:---:|:---:|---|
| `validador.py` | 37 | 16 | **100%** | Ninguna (totalmente cubierto) |
| `database.py` | 22 | 4 | **100%** | Ninguna (totalmente cubierto) |
| `repositorio.py` | 45 | 4 | **96%** | `76` (manejo defensivo de error) |
| `routes.py` | 97 | 38 | **90%** | `16-21`, `33`, `60` |
| `servicio.py` | 27 | 8 | **89%** | `37` |
| `app.py` | 40 | 2 | **86%** | `48`, `60`, `66-69` (arranque `__main__`) |
| `reloj.py` | 6 | 0 | **83%** | `14` (`RelojSistema.hoy()`) |
| **TOTAL** | **613** | **84** | **92%** | *(Ver volcado en Anexo A.4)* |

- **Cobertura global:** **92%** combinada (**100%** en componentes de dominio `validador.py` y `database.py`).

### Análisis de líneas sin cubrir y decisiones
- `validador.py:19`: Se cubrió la rama defensiva no-diccionario mediante `test_validador_rechaza_cuerpo_no_diccionario` con TDD, logrando el 100%.
- `reloj.py:14`: Retorno de `RelojSistema`. Decisión: no cubrir para garantizar determinismo temporal.
- `app.py:66-69`: Bloque `__main__`. Decisión: rama inalcanzable en pruebas que usan la fábrica `create_app()`.
- `routes.py:16-21`: Fallback fuera de contexto. Decisión: no justificado forzar pruebas fuera del framework.

### Qué dice y qué NO dice la cobertura (Ley de Goodhart y Valores Límite)
- **Qué dice:** Certifica de forma objetiva qué líneas y bifurcaciones fueron transitadas durante la ejecución de las pruebas.
- **Qué NO dice:** No garantiza ausencia de defectos (Principio 1 de ISTQB). Si se escribe `>` en vez de `>=`, pruebas con 1 y 10 caracteres alcanzan **100% de cobertura de ramas sin detectar el defecto**. Solo los valores límite ($2, 3, 50, 51$ y hoy/mañana) detectan el error de frontera.
- **Ley de Goodhart:** *"Cuando una métrica se convierte en meta, deja de ser una buena métrica"*. Perseguir el 100% forzando pruebas artificiales sobre handlers o scripts solo añade fragilidad sin valor de verificación.

---

## Anexo A. Evidencias de ejecución

### A.1. Plan de Pruebas de Integración (Fase B)

| Endpoint | Caso | HTTP | Verificación del cuerpo | Efecto en persistencia (SQLite) | Categoría de frontera |
|---|---|:---:|---|---|---|
| `POST /avistamientos` | Creación exitosa | 201 | Objeto creado con `id` asignado | `INSERT` confirmado; consultable con GET | Consultas y mapeo / Transacciones |
| `POST /avistamientos` | Especie corta (< 3 car) | 400 | Error nombrando `especie` | Tabla permanece vacía | Contratos de datos |
| `POST /avistamientos` | Fecha posterior a hoy | 400 | Error nombrando `fecha` | Tabla permanece vacía | Formatos y unidades |
| `POST /avistamientos` | Lugar vacío | 400 | Error nombrando `lugar` | Tabla permanece vacía | Contratos de datos |
| `GET /avistamientos` | Lista vacía | 200 | Lista vacía `[]` | `SELECT` en tabla vacía | Consultas y mapeo |
| `GET /avistamientos` | Lista con registros | 200 | Lista ordenada por `id ASC` | `SELECT ... ORDER BY id ASC` | Consultas y mapeo |
| `GET /avistamientos/<id>`| Id existente | 200 | Objeto correspondiente | `SELECT ... WHERE id = ?` | Consultas y mapeo |
| `GET /avistamientos/<id>`| Id inexistente | 404 | Error recurso no encontrado | `SELECT` retorna `None` | Consultas y mapeo |
| `PUT /avistamientos/<id>`| Actualización exitosa | 200 | Objeto con datos mutados | `UPDATE` confirmado; GET refleja cambios | Consultas y mapeo / Transacciones |
| `PUT /avistamientos/<id>`| Especie corta (< 3 car) | 400 | Error nombrando `especie` | Registro previo permanece intacto | Contratos de datos |
| `PUT /avistamientos/<id>`| Fecha futura | 400 | Error nombrando `fecha` | Registro previo permanece intacto | Formatos y unidades |
| `DELETE /avistamientos/<id>`| Eliminación exitosa | 204 | Cuerpo vacío | `DELETE` confirmado; posterior GET da 404 | Consultas y mapeo / Transacciones |
| `GET /avistamientos/resumen`| Resumen con datos | 200 | Diccionario agrupado | `GROUP BY especie` real | Consultas y mapeo |

### A.2. Catálogo completo de casos de prueba de la validación (Parte A)

| Campo | Partición / Límite | Valor | Resultado | Justificación técnica |
|---|---|---|---|---|
| `especie` | Límite inferior $-1$ | `"ab"` | Inválido (400) | Longitud 2 (< 3) |
| `especie` | Límite inferior exacto | `"ave"` | Válido | Longitud 3 (frontera mínima) |
| `especie` | Representativo válido | `"colibrí"` | Válido | Longitud 7 (en rango $[3, 50]$) |
| `especie` | Límite superior exacto | `"a"*50` | Válido | Longitud 50 (frontera máxima) |
| `especie` | Límite superior $+1$ | `"a"*51` | Inválido (400) | Longitud 51 (> 50) |
| `especie` | Espacios en extremos | `"  ab  "` | Inválido (400) | Longitud efectiva 2 tras `strip()` |
| `especie` | Cadena vacía | `""` | Inválido (400) | Partición vacía |
| `especie` | Solo espacios | `"   "` | Inválido (400) | Partición espacios |
| `especie` | Tipo no string (nulo) | `None` | Inválido (400) | Tipo inválido |
| `especie` | Tipo numérico | `123` | Inválido (400) | Tipo inválido |
| `fecha` | Pasado representativo | `"2026-05-10"` | Válido | Fecha pasada válida |
| `fecha` | Bisiesto pasado válido | `"2024-02-29"` | Válido | 2024 fue bisiesto |
| `fecha` | Ayer | `"2026-10-20"` | Válido | Hoy $-1$ |
| `fecha` | Hoy | `"2026-10-21"` | Válido | Límite superior permitido |
| `fecha` | Mañana | `"2026-10-22"` | Inválido (400) | Hoy $+1$ (futuro no permitido) |
| `fecha` | Bisiesto en año común | `"2026-02-29"` | Inválido (400) | 2026 no es bisiesto |
| `fecha` | Día inexistente | `"2026-02-30"` | Inválido (400) | Fecha inexistente |
| `fecha` | Mes inexistente | `"2026-13-45"` | Inválido (400) | Formato/mes inválido |
| `fecha` | Formato incorrecto | `"21/10/2026"` | Inválido (400) | Formato no AAAA-MM-DD |
| `fecha` | Con espacios al final | `"2026-10-21 "` | Inválido (400) | Espacio rompe formato estricto |
| `lugar` | Representativo válido | `"Jardín Botánico"` | Válido | No vacío |
| `lugar` | Límite mínimo ($n=1$) | `"A"` | Válido | 1 carácter no vacío |
| `lugar` | Cadena vacía | `""` | Inválido (400) | Partición vacía |
| `lugar` | Solo espacios | `"   "` | Inválido (400) | Partición espacios |
| `lugar` | Tipo nulo | `None` | Inválido (400) | Tipo inválido |
| `lugar` | Tipo numérico | `123` | Inválido (400) | Tipo inválido |
| `observador` | Representativo válido | `"Carlos Ruiz"` | Válido | No vacío |
| `observador` | Límite mínimo ($n=1$) | `"O"` | Válido | 1 carácter no vacío |
| `observador` | Cadena vacía | `""` | Inválido (400) | Partición vacía |
| `observador` | Solo espacios | `"   "` | Inválido (400) | Partición espacios |
| `observador` | Tipo nulo | `None` | Inválido (400) | Tipo inválido |
| `observador` | Tipo numérico | `456` | Inválido (400) | Tipo inválido |
| Caso general | Avistamiento completo | Datos válidos | Válido | Todos los campos cumplen |

### A.3. Prueba de independencia: Ejecución de integración en orden inverso
Se verificó la independencia de las pruebas de integración ejecutándolas en orden inverso, confirmando que cada una inicializa y limpia su propia base de datos temporal provista por `tmp_path`:

```text
tests/test_api.py::test_put_rechaza_fecha_futura_regla_nueva PASSED      [  4%]
tests/test_api.py::test_put_rechaza_especie_corta_regla_nueva PASSED     [  8%]
tests/test_api.py::test_post_rechaza_lugar_vacio_regla_nueva PASSED      [ 12%]
tests/test_api.py::test_post_rechaza_fecha_futura_regla_nueva PASSED     [ 16%]
tests/test_api.py::test_post_rechaza_especie_corta_regla_nueva PASSED    [ 20%]
tests/test_api.py::test_metodo_no_permitido_devuelve_405_json PASSED     [ 24%]
tests/test_api.py::test_resumen_con_multiples_especies PASSED            [ 28%]
tests/test_api.py::test_resumen_vacio PASSED                             [ 32%]
tests/test_api.py::test_put_con_datos_invalidos PASSED                   [ 36%]
tests/test_api.py::test_post_ignora_id_enviado_por_cliente PASSED        [ 40%]
tests/test_api.py::test_post_cuerpo_no_objeto PASSED                     [ 44%]
tests/test_api.py::test_post_cuerpo_json_malformado PASSED               [ 48%]
tests/test_api.py::test_post_fecha_formato_incorrecto PASSED             [ 52%]
tests/test_api.py::test_post_fecha_invalida_mes_o_dia_inexistente PASSED [ 56%]
tests/test_api.py::test_post_campo_vacio_o_espacios PASSED               [ 60%]
tests/test_api.py::test_post_campos_faltantes PASSED                     [ 64%]
tests/test_api.py::test_ruta_no_existente_devuelve_404_json PASSED       [ 68%]
tests/test_api.py::test_delete_id_inexistente PASSED                     [ 72%]
tests/test_api.py::test_put_id_inexistente PASSED                        [ 76%]
tests/test_api.py::test_get_id_inexistente PASSED                        [ 80%]
tests/test_api.py::test_eliminar_avistamiento_y_confirmar_inexistencia PASSED [ 84%]
tests/test_api.py::test_actualizar_avistamiento_exitoso PASSED           [ 88%]
tests/test_api.py::test_obtener_un_avistamiento_exitoso PASSED           [ 92%]
tests/test_api.py::test_crear_avistamiento_exitoso PASSED                [ 96%]
tests/test_api.py::test_listar_avistamientos_vacio PASSED                [100%]
============================= 25 passed in 0.83s ==============================
```

### A.4. Salida completa de cobertura de la suite
Volcado textual emitido por la herramienta `pytest-cov` en consola:

```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\aulainformatica\Desktop\ApiSoftware-main\ApiSoftware-main
plugins: cov-7.1.0
collected 59 items

tests\test_api.py .........................                              [ 42%]
tests\test_unitarias.py ..................................               [100%]

=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.14.6-final-0 _______________

Name                      Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------------------
app.py                       40      5      2      1    86%   48, 60, 66-69
database.py                  22      0      4      0   100%
reloj.py                      6      1      0      0    83%   14
repositorio.py               45      1      4      1    96%   76
routes.py                    97      7     38      6    90%   16-21, 33, 60, 118->127, 146->155
servicio.py                  27      1      8      3    89%   27->31, 34->38, 37
tests\__init__.py             0      0      0      0   100%
tests\test_api.py           187      0      2      0   100%
tests\test_unitarias.py     152     18     10      0    83%   341-344, 353-358, 361-363, 366-370
validador.py                 37      0     16      0   100%
---------------------------------------------------------------------
TOTAL                       613     33     84     11    92%
============================= 59 passed in 1.31s ==============================
```
