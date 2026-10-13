# API REST de Avistamiento de Aves

Proyecto para **Ingeniería de Software 2**.  
Consiste en una API RESTful desarrollada en Python con Flask para la gestión y seguimiento del registro de avistamientos de aves. La persistencia se realiza mediante SQLite embebido utilizando exclusivamente el módulo estándar `sqlite3` (sin ORM), aplicando buenas prácticas de diseño de software como el patrón *Application Factory*, validaciones rigurosas y pruebas automatizadas con `pytest`.

---

## 1. Requisitos
- **Python:** 3.10 o superior (verificado con Python 3.12).
- Gestor de paquetes **pip**.

---

## 2. Instalación y Ejecución Paso a Paso

### En Windows (PowerShell)
1. Abrir PowerShell y ubicarse en la carpeta raíz del proyecto (ejemplo de ruta):
   ```powershell
   cd /ruta/hacia/Api
   ```
2. Crear un entorno virtual limpio:
   ```powershell
   python -m venv venv
   ```
3. Activar el entorno virtual:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   *(Nota: si PowerShell bloquea la ejecución de scripts por ExecutionPolicy, ejecutar temporalmente `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`).*
4. Instalar las dependencias mínimas requeridas:
   ```powershell
   pip install -r requirements.txt
   ```
5. Iniciar la API:
   ```powershell
   python app.py
   ```
   El servidor quedará disponible en: `http://127.0.0.1:5000`

---

### En Linux / macOS (Bash o Zsh)
1. Abrir la terminal y ubicarse en la carpeta raíz del proyecto:
   ```bash
   cd /ruta/hacia/Api
   ```
2. Crear un entorno virtual:
   ```bash
   python3 -m venv venv
   ```
3. Activar el entorno virtual:
   ```bash
   source venv/bin/activate
   ```
4. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
5. Ejecutar la aplicación:
   ```bash
   python3 app.py
   ```
   El servidor quedará disponible en: `http://127.0.0.1:5000`

> **Nota sobre la base de datos:** El archivo `avistamientos.db` se crea automáticamente la primera vez que se inicia la aplicación. No requiere ejecutar migraciones ni scripts adicionales.

---

## 3. Ejecución de Pruebas Automatizadas

Las pruebas unitarias y de integración se ejecutan de forma aislada utilizando una base de datos SQLite temporal en memoria/directorio temporal proporcionada por el fixture `tmp_path` de `pytest`.

Con el entorno virtual activado, ejecutar:
```bash
pytest -v
```
Para ver el resumen con detalle de cobertura y tiempos:
```bash
pytest -v --durations=5
```

---

## 4. Tabla de Endpoints

Todos los endpoints responden con `Content-Type: application/json` (a excepción del código `204 No Content` que no incluye cuerpo).

| Método | Endpoint | Descripción | Códigos de Estado Posibles |
|---|---|---|---|
| `GET` | `/avistamientos` | Lista todos los avistamientos registrados en orden ascendente por ID. | `200 OK` |
| `GET` | `/avistamientos/<int:id>` | Obtiene el detalle de un avistamiento específico por su ID numérico. | `200 OK`, `404 Not Found` |
| `POST` | `/avistamientos` | Registra un nuevo avistamiento de ave. Asigna el ID automáticamente. | `201 Created`, `400 Bad Request` |
| `PUT` | `/avistamientos/<int:id>` | Actualiza todos los campos de un avistamiento existente. | `200 OK`, `400 Bad Request`, `404 Not Found` |
| `DELETE` | `/avistamientos/<int:id>` | Elimina un avistamiento existente del sistema. | `204 No Content`, `404 Not Found` |
| `GET` | `/avistamientos/resumen` | Genera un reporte agrupado con la cantidad de avistamientos por especie. | `200 OK` |

Cualquier ruta inexistente o método HTTP no permitido responderá en JSON con formato uniforme:
```json
{
  "error": "Mensaje descriptivo del error"
}
```

---

## 5. Ejemplos de Peticiones con `curl`

### 1. Listar todos los avistamientos (`GET /avistamientos`)

**Windows (PowerShell):**
```powershell
curl.exe -X GET http://127.0.0.1:5000/avistamientos
```

**Linux / macOS / Git Bash:**
```bash
curl -X GET http://127.0.0.1:5000/avistamientos
```

**Respuesta esperada (200 OK):**
```json
[]
```
*(O una lista con los objetos registrados si ya hay datos).*

---

### 2. Registrar un nuevo avistamiento (`POST /avistamientos`)

**Windows (PowerShell):**
```powershell
curl.exe -X POST http://127.0.0.1:5000/avistamientos -H "Content-Type: application/json" -d '{\"especie\": \"colibrí\", \"lugar\": \"Jardín Botánico\", \"fecha\": \"2026-05-10\", \"observador\": \"Carlos Ruiz\"}'
```

**Linux / macOS / Git Bash:**
```bash
curl -X POST http://127.0.0.1:5000/avistamientos -H "Content-Type: application/json" -d '{"especie": "colibrí", "lugar": "Jardín Botánico", "fecha": "2026-05-10", "observador": "Carlos Ruiz"}'
```

**Respuesta esperada (201 Created):**
```json
{
  "id": 1,
  "especie": "colibrí",
  "lugar": "Jardín Botánico",
  "fecha": "2026-05-10",
  "observador": "Carlos Ruiz"
}
```

---

### 3. Obtener un avistamiento por ID (`GET /avistamientos/<id>`)

**Windows (PowerShell):**
```powershell
curl.exe -X GET http://127.0.0.1:5000/avistamientos/1
```

**Linux / macOS / Git Bash:**
```bash
curl -X GET http://127.0.0.1:5000/avistamientos/1
```

**Respuesta esperada (200 OK):**
```json
{
  "id": 1,
  "especie": "colibrí",
  "lugar": "Jardín Botánico",
  "fecha": "2026-05-10",
  "observador": "Carlos Ruiz"
}
```

**Si el ID no existe (404 Not Found):**

*Windows (PowerShell):*
```powershell
curl.exe -X GET http://127.0.0.1:5000/avistamientos/999
```

*Linux / macOS / Git Bash:*
```bash
curl -X GET http://127.0.0.1:5000/avistamientos/999
```

**Respuesta:**
```json
{
  "error": "No se encontró el avistamiento con id 999."
}
```

---

### 4. Actualizar un avistamiento existente (`PUT /avistamientos/<id>`)

**Windows (PowerShell):**
```powershell
curl.exe -X PUT http://127.0.0.1:5000/avistamientos/1 -H "Content-Type: application/json" -d '{\"especie\": \"colibrí coliazul\", \"lugar\": \"Jardín Botánico - Sendero A\", \"fecha\": \"2026-05-11\", \"observador\": \"Carlos Ruiz\"}'
```

**Linux / macOS / Git Bash:**
```bash
curl -X PUT http://127.0.0.1:5000/avistamientos/1 -H "Content-Type: application/json" -d '{"especie": "colibrí coliazul", "lugar": "Jardín Botánico - Sendero A", "fecha": "2026-05-11", "observador": "Carlos Ruiz"}'
```

**Respuesta esperada (200 OK):**
```json
{
  "id": 1,
  "especie": "colibrí coliazul",
  "lugar": "Jardín Botánico - Sendero A",
  "fecha": "2026-05-11",
  "observador": "Carlos Ruiz"
}
```

---

### 5. Resumen de avistamientos por especie (`GET /avistamientos/resumen`)

**Windows (PowerShell):**
```powershell
curl.exe -X GET http://127.0.0.1:5000/avistamientos/resumen
```

**Linux / macOS / Git Bash:**
```bash
curl -X GET http://127.0.0.1:5000/avistamientos/resumen
```

**Respuesta esperada (200 OK):**
```json
{
  "colibrí coliazul": 1
}
```

---

### 6. Eliminar un avistamiento (`DELETE /avistamientos/<id>`)

**Windows (PowerShell):**
```powershell
curl.exe -X DELETE -i http://127.0.0.1:5000/avistamientos/1
```

**Linux / macOS / Git Bash:**
```bash
curl -X DELETE -i http://127.0.0.1:5000/avistamientos/1
```

**Respuesta esperada (204 No Content):**
```http
HTTP/1.1 204 NO CONTENT
```
*(Cuerpo vacío).*

---

### 7. Ejemplo de error de validación (400 Bad Request con fecha inválida)

**Windows (PowerShell):**
```powershell
curl.exe -X POST http://127.0.0.1:5000/avistamientos -H "Content-Type: application/json" -d '{\"especie\": \"águila\", \"lugar\": \"Cañón\", \"fecha\": \"2026-13-45\", \"observador\": \"Ana\"}'
```

**Linux / macOS / Git Bash:**
```bash
curl -X POST http://127.0.0.1:5000/avistamientos -H "Content-Type: application/json" -d '{"especie": "águila", "lugar": "Cañón", "fecha": "2026-13-45", "observador": "Ana"}'
```

**Respuesta (400 Bad Request):**
```json
{
  "error": "El campo 'fecha' debe cumplir exactamente el formato AAAA-MM-DD y ser una fecha válida."
}
```

---

## 6. Estructura del Proyecto

```text
Api/
├── app.py              # Fábrica create_app(), configuración y manejadores de error globales
├── database.py         # Conexión get_db(), cierre close_db() e inicialización init_db()
├── routes.py           # Blueprint de Flask con endpoints y funciones de validación
├── requirements.txt    # Dependencias mínimas (Flask, pytest)
├── .gitignore          # Exclusión de venv, __pycache__, bases .db y caché de pytest
├── README.md           # Documentación técnica, guía de uso y ejemplos
└── tests/
    ├── __init__.py     # Inicializador del paquete de pruebas
    └── test_api.py     # Suite de pruebas unitarias y de integración con pytest
```

---

## 7. Uso de Inteligencia Artificial

Este proyecto se desarrolló con ayuda de Gemini 3.8 Flash high usando el IDE de Antigravity El código fue revisado y comprendido por el autor.

---

## 8. Autor

Samuel Andres Mesa Comaz 
Estudiante de Ingeniería de Software  
Universidad: Universidad El Bosque
