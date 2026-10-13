import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    """
    Fixture de pytest que crea una instancia de la aplicación Flask
    utilizando una base de datos SQLite temporal y aislada en cada prueba.
    """
    db_file = tmp_path / "test_avistamientos.db"
    app = create_app(db_path=db_file)
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


# ==========================================
# 1. Pruebas de casos exitosos (200, 201, 204)
# ==========================================

def test_listar_avistamientos_vacio(client):
    """Verifica que GET /avistamientos devuelva 200 y una lista vacía cuando no hay registros."""
    response = client.get("/avistamientos")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.get_json() == []


def test_crear_avistamiento_exitoso(client):
    """Verifica que POST /avistamientos devuelva 201 y el recurso creado con su ID autoincremental."""
    payload = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": "2026-05-10",
        "observador": "Carlos Ruiz"
    }
    response = client.post("/avistamientos", json=payload)
    assert response.status_code == 201
    assert response.headers["Content-Type"] == "application/json"
    data = response.get_json()
    assert data["id"] == 1
    assert data["especie"] == "colibrí"
    assert data["lugar"] == "Jardín Botánico"
    assert data["fecha"] == "2026-05-10"
    assert data["observador"] == "Carlos Ruiz"


def test_obtener_un_avistamiento_exitoso(client):
    """Verifica que GET /avistamientos/<id> devuelva 200 y el objeto correspondiente."""
    # Creamos un registro previo
    post_res = client.post("/avistamientos", json={
        "especie": "águila real",
        "lugar": "Cañón del Chicamocha",
        "fecha": "2026-06-15",
        "observador": "Lucía Gómez"
    })
    creado = post_res.get_json()

    response = client.get(f"/avistamientos/{creado['id']}")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    data = response.get_json()
    assert data == creado


def test_actualizar_avistamiento_exitoso(client):
    """Verifica que PUT /avistamientos/<id> devuelva 200 y el objeto actualizado."""
    # Registro inicial
    post_res = client.post("/avistamientos", json={
        "especie": "carpintero",
        "lugar": "Bosque de Niebla",
        "fecha": "2026-04-01",
        "observador": "Mario"
    })
    creado = post_res.get_json()

    # Actualización con nuevos datos
    nuevos_datos = {
        "especie": "pájaro carpintero copetón",
        "lugar": "Bosque de Niebla - Sendero 3",
        "fecha": "2026-04-02",
        "observador": "Mario López"
    }
    response = client.put(f"/avistamientos/{creado['id']}", json=nuevos_datos)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    data = response.get_json()
    assert data["id"] == creado["id"]
    assert data["especie"] == "pájaro carpintero copetón"
    assert data["lugar"] == "Bosque de Niebla - Sendero 3"
    assert data["fecha"] == "2026-04-02"
    assert data["observador"] == "Mario López"


def test_eliminar_avistamiento_y_confirmar_inexistencia(client):
    """Verifica que DELETE devuelva 204 sin cuerpo y que posteriores GET devuelvan 404."""
    post_res = client.post("/avistamientos", json={
        "especie": "tucán",
        "lugar": "Parque Tayrona",
        "fecha": "2026-07-20",
        "observador": "Sofía"
    })
    item_id = post_res.get_json()["id"]

    # Eliminar
    delete_res = client.delete(f"/avistamientos/{item_id}")
    assert delete_res.status_code == 204
    assert delete_res.data == b""

    # Confirmar que ya no existe (debe dar 404)
    get_res = client.get(f"/avistamientos/{item_id}")
    assert get_res.status_code == 404
    assert "error" in get_res.get_json()


# ==========================================
# 2. Pruebas de recursos no encontrados (404)
# ==========================================

def test_get_id_inexistente(client):
    """Verifica que GET /avistamientos/<id> con ID inexistente devuelva 404 y JSON de error."""
    response = client.get("/avistamientos/999")
    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/json"
    data = response.get_json()
    assert "error" in data


def test_put_id_inexistente(client):
    """Verifica que PUT /avistamientos/<id> con ID inexistente devuelva 404 y JSON de error."""
    payload = {
        "especie": "canario",
        "lugar": "Parque Central",
        "fecha": "2026-08-01",
        "observador": "Andrés"
    }
    response = client.put("/avistamientos/999", json=payload)
    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/json"
    data = response.get_json()
    assert "error" in data


def test_delete_id_inexistente(client):
    """Verifica que DELETE /avistamientos/<id> con ID inexistente devuelva 404 y JSON de error."""
    response = client.delete("/avistamientos/999")
    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/json"
    data = response.get_json()
    assert "error" in data


def test_ruta_no_existente_devuelve_404_json(client):
    """Verifica que rutas no registradas respondan 404 en formato JSON y no HTML."""
    response = client.get("/ruta-totalmente-inexistente")
    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/json"
    data = response.get_json()
    assert "error" in data


# ==========================================
# 3. Pruebas de validación en POST (400)
# ==========================================

def test_post_campos_faltantes(client):
    """Verifica que falte un campo obligatorio devuelva 400."""
    payload = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": "2026-05-10"
        # Falta "observador"
    }
    response = client.post("/avistamientos", json=payload)
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/json"
    assert "observador" in response.get_json()["error"]


def test_post_campo_vacio_o_espacios(client):
    """Verifica que enviar un campo vacío o solo con espacios devuelva 400."""
    payload = {
        "especie": "   ",
        "lugar": "Jardín Botánico",
        "fecha": "2026-05-10",
        "observador": "Carlos"
    }
    response = client.post("/avistamientos", json=payload)
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/json"
    assert "error" in response.get_json()


def test_post_fecha_invalida_mes_o_dia_inexistente(client):
    """Verifica que una fecha imposible (ej. 2026-13-45) devuelva 400."""
    payload = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": "2026-13-45",
        "observador": "Carlos"
    }
    response = client.post("/avistamientos", json=payload)
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/json"
    assert "fecha" in response.get_json()["error"]


def test_post_fecha_formato_incorrecto(client):
    """Verifica que fechas con formato distinto a AAAA-MM-DD devuelvan 400."""
    payload = {
        "especie": "colibrí",
        "lugar": "Jardín Botánico",
        "fecha": "10/05/2026",
        "observador": "Carlos"
    }
    response = client.post("/avistamientos", json=payload)
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/json"
    assert "fecha" in response.get_json()["error"]


def test_post_cuerpo_json_malformado(client):
    """Verifica que enviar texto sin formato JSON válido devuelva 400 en JSON."""
    response = client.post(
        "/avistamientos",
        data="{esto_no_es_un_json_valido}",
        content_type="application/json"
    )
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/json"
    assert "error" in response.get_json()


def test_post_cuerpo_no_objeto(client):
    """Verifica que enviar una lista JSON o valor primitivo devuelva 400."""
    response = client.post("/avistamientos", json=["colibrí", "bosque"])
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/json"
    assert "error" in response.get_json()


def test_post_ignora_id_enviado_por_cliente(client):
    """Verifica que si el cliente envía un 'id' en el cuerpo, la API lo ignore y asigne el autoincremental."""
    payload = {
        "id": 9999,
        "especie": "lechuza",
        "lugar": "Campanario",
        "fecha": "2026-09-15",
        "observador": "Elena"
    }
    response = client.post("/avistamientos", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 1  # Primer registro autoincremental asignado por la BD, no 9999
    assert data["especie"] == "lechuza"


# ==========================================
# 4. Pruebas de validación en PUT (400)
# ==========================================

def test_put_con_datos_invalidos(client):
    """Verifica que enviar datos inválidos a un recurso existente devuelva 400."""
    post_res = client.post("/avistamientos", json={
        "especie": "gaviota",
        "lugar": "Puerto",
        "fecha": "2026-03-12",
        "observador": "Raúl"
    })
    item_id = post_res.get_json()["id"]

    # Enviamos campo faltante
    put_res = client.put(f"/avistamientos/{item_id}", json={
        "especie": "gaviota",
        "lugar": "Puerto"
    })
    assert put_res.status_code == 400
    assert put_res.headers["Content-Type"] == "application/json"
    assert "error" in put_res.get_json()


# ==========================================
# 5. Endpoint de resumen y no colisión de rutas
# ==========================================

def test_resumen_vacio(client):
    """Verifica que GET /avistamientos/resumen devuelva un objeto vacío {} cuando no hay datos."""
    response = client.get("/avistamientos/resumen")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.get_json() == {}


def test_resumen_con_multiples_especies(client):
    """Verifica que GET /avistamientos/resumen agrupe y cuente correctamente por especie."""
    # Insertamos 3 colibríes, 1 águila y 2 gorriones
    avistamientos = [
        {"especie": "colibrí", "lugar": "Zona A", "fecha": "2026-01-10", "observador": "Obs 1"},
        {"especie": "colibrí", "lugar": "Zona B", "fecha": "2026-01-11", "observador": "Obs 2"},
        {"especie": "colibrí", "lugar": "Zona C", "fecha": "2026-01-12", "observador": "Obs 3"},
        {"especie": "águila", "lugar": "Montaña", "fecha": "2026-02-01", "observador": "Obs 1"},
        {"especie": "gorrión", "lugar": "Parque", "fecha": "2026-02-05", "observador": "Obs 2"},
        {"especie": "gorrión", "lugar": "Plaza", "fecha": "2026-02-06", "observador": "Obs 3"}
    ]
    for item in avistamientos:
        res = client.post("/avistamientos", json=item)
        assert res.status_code == 201

    response = client.get("/avistamientos/resumen")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    data = response.get_json()
    assert data == {
        "colibrí": 3,
        "gorrión": 2,
        "águila": 1
    }


def test_metodo_no_permitido_devuelve_405_json(client):
    """Verifica que llamar un método no soportado (ej. POST a /avistamientos/resumen) responda 405 en JSON."""
    response = client.post("/avistamientos/resumen", json={"test": "data"})
    assert response.status_code == 405
    assert response.headers["Content-Type"] == "application/json"
    data = response.get_json()
    assert "error" in data
