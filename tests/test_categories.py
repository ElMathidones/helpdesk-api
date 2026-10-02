from app.models.enums import UserRole
from app.models.user import User


def login_user(client, email: str, password: str = "senha123") -> str:
    response = client.post(
        "/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def test_admin_can_create_category(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    token = login_user(client, "admin@example.com")

    response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Hardware"
    assert data["is_active"] is True


def test_customer_cannot_create_category(client):
    client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

    token = login_user(client, "cliente@example.com")

    response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


def test_duplicate_category_returns_conflict(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    token = login_user(client, "admin@example.com")

    payload = {
        "name": "Hardware",
        "description": "Problemas de hardware",
    }

    first_response = client.post(
        "/categories",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    second_response = client.post(
        "/categories",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {"detail": "Category already exists"}


def test_authenticated_user_can_list_categories(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    admin_token = login_user(client, "admin@example.com")

    client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

    customer_token = login_user(client, "cliente@example.com")

    response = client.get(
        "/categories",
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Hardware"


def test_list_categories_without_token_returns_401(client):
    response = client.get("/categories")

    assert response.status_code == 401


def test_admin_can_update_category(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    token = login_user(client, "admin@example.com")

    create_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    category_id = create_response.json()["id"]

    response = client.patch(
        f"/categories/{category_id}",
        json={
            "name": "Hardware e Periféricos",
            "description": "Problemas de hardware e periféricos",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category_id
    assert data["name"] == "Hardware e Periféricos"
    assert data["description"] == "Problemas de hardware e periféricos"
    assert data["is_active"] is True


def test_admin_can_clear_category_description(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    token = login_user(client, "admin@example.com")

    create_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    category_id = create_response.json()["id"]

    response = client.patch(
        f"/categories/{category_id}",
        json={
            "description": None,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_update_category_with_duplicate_name_returns_conflict(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    token = login_user(client, "admin@example.com")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    first_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": None,
        },
        headers=headers,
    )

    client.post(
        "/categories",
        json={
            "name": "Rede",
            "description": None,
        },
        headers=headers,
    )

    category_id = first_response.json()["id"]

    response = client.patch(
        f"/categories/{category_id}",
        json={
            "name": "Rede",
        },
        headers=headers,
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Category already exists"}


def test_update_nonexistent_category_returns_404(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    token = login_user(client, "admin@example.com")

    response = client.patch(
        "/categories/999999",
        json={
            "name": "Categoria Teste",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Category not found"}


def test_customer_cannot_update_category(client):
    client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

    token = login_user(client, "cliente@example.com")

    response = client.patch(
        "/categories/1",
        json={
            "name": "Categoria Alterada",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


def test_technician_cannot_update_category(client, db):
    client.post(
        "/users",
        json={
            "name": "Técnico Teste",
            "email": "tecnico@example.com",
            "password": "senha123",
        },
    )

    technician = db.query(User).filter(User.email == "tecnico@example.com").first()

    assert technician is not None

    technician.role = UserRole.TECHNICIAN
    db.commit()

    token = login_user(client, "tecnico@example.com")

    response = client.patch(
        "/categories/1",
        json={
            "name": "Categoria Alterada",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


def test_admin_can_deactivate_and_reactivate_category(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    token = login_user(client, "admin@example.com")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    create_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers=headers,
    )

    assert create_response.status_code == 201

    category_id = create_response.json()["id"]

    deactivate_response = client.patch(
        f"/categories/{category_id}/status",
        json={
            "is_active": False,
        },
        headers=headers,
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    reactivate_response = client.patch(
        f"/categories/{category_id}/status",
        json={
            "is_active": True,
        },
        headers=headers,
    )

    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["is_active"] is True


def test_customer_cannot_update_category_status(client):
    client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

    token = login_user(client, "cliente@example.com")

    response = client.patch(
        "/categories/1/status",
        json={
            "is_active": False,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Insufficient permissions",
    }


def test_update_nonexistent_category_status_returns_404(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    token = login_user(client, "admin@example.com")

    response = client.patch(
        "/categories/999999/status",
        json={
            "is_active": False,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Category not found",
    }


def test_admin_can_reorder_categories(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    token = login_user(client, "admin@example.com")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    first_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": None,
        },
        headers=headers,
    )

    second_response = client.post(
        "/categories",
        json={
            "name": "Software",
            "description": None,
        },
        headers=headers,
    )

    third_response = client.post(
        "/categories",
        json={
            "name": "Rede",
            "description": None,
        },
        headers=headers,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert third_response.status_code == 201

    hardware_id = first_response.json()["id"]
    software_id = second_response.json()["id"]
    network_id = third_response.json()["id"]

    response = client.put(
        "/categories/order",
        json={
            "category_ids": [
                network_id,
                hardware_id,
                software_id,
            ],
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert [category["id"] for category in data] == [
        network_id,
        hardware_id,
        software_id,
    ]


def test_reorder_categories_rejects_missing_category(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    token = login_user(client, "admin@example.com")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    first_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": None,
        },
        headers=headers,
    )

    client.post(
        "/categories",
        json={
            "name": "Software",
            "description": None,
        },
        headers=headers,
    )

    category_id = first_response.json()["id"]

    response = client.put(
        "/categories/order",
        json={
            "category_ids": [category_id],
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Category order must include all categories",
    }


def test_reorder_categories_rejects_duplicate_ids(client, db):
    client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin = db.query(User).filter(User.email == "admin@example.com").first()

    assert admin is not None

    admin.role = UserRole.ADMIN
    db.commit()

    token = login_user(client, "admin@example.com")

    headers = {
        "Authorization": f"Bearer {token}",
    }

    create_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": None,
        },
        headers=headers,
    )

    category_id = create_response.json()["id"]

    response = client.put(
        "/categories/order",
        json={
            "category_ids": [
                category_id,
                category_id,
            ],
        },
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Category order contains duplicate ids",
    }


def test_customer_cannot_reorder_categories(client):
    client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

    token = login_user(client, "cliente@example.com")

    response = client.put(
        "/categories/order",
        json={
            "category_ids": [1],
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Insufficient permissions",
    }
