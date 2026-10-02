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
