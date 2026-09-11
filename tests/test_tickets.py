from app.models.enums import TicketStatus, UserRole
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

    user = db.query(User).filter(User.email == "admin@example.com").first()

    assert user is not None

    user.role = UserRole.ADMIN
    db.commit()

    login_response = client.post(
        "/auth/login",
        data={
            "username": "admin@example.com",
            "password": "senha123",
        },
    )

    token = login_response.json()["access_token"]

    category_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert category_response.status_code == 201

    data = category_response.json()

    assert data["name"] == "Hardware"
    assert data["is_active"] is True


def test_create_ticket(client):
    user_response = client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

    assert user_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={
            "username": "cliente@example.com",
            "password": "senha123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    category_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert category_response.status_code == 403


def test_customer_can_create_ticket(client, db):
    client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

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

    category_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert category_response.status_code == 201

    category_id = category_response.json()["id"]

    customer_token = login_user(client, "cliente@example.com")

    response = client.post(
        "/tickets",
        json={
            "title": "Computador não liga",
            "description": "O computador não apresenta nenhum sinal.",
            "priority": "high",
            "category_id": category_id,
        },
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Computador não liga"
    assert data["priority"] == "high"
    assert data["status"] == "open"
    assert data["assignee_id"] is None


def test_customer_cannot_assign_ticket(client, db):
    client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

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

    category_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    category_id = category_response.json()["id"]

    customer_token = login_user(client, "cliente@example.com")

    ticket_response = client.post(
        "/tickets",
        json={
            "title": "Erro de rede",
            "description": "O computador está sem acesso à internet.",
            "priority": "medium",
            "category_id": category_id,
        },
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    ticket_id = ticket_response.json()["id"]

    response = client.patch(
        f"/tickets/{ticket_id}/assign",
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


def test_admin_can_assign_ticket(client, db):
    client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

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

    category_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    category_id = category_response.json()["id"]

    customer_token = login_user(client, "cliente@example.com")

    ticket_response = client.post(
        "/tickets",
        json={
            "title": "Erro de rede",
            "description": "O computador está sem acesso à internet.",
            "priority": "medium",
            "category_id": category_id,
        },
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    ticket_id = ticket_response.json()["id"]

    response = client.patch(
        f"/tickets/{ticket_id}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["assignee_id"] == admin.id
    assert data["status"] == TicketStatus.IN_PROGRESS


def test_customer_cannot_view_another_customers_ticket(client, db):
    client.post(
        "/users",
        json={
            "name": "Cliente Um",
            "email": "cliente1@example.com",
            "password": "senha123",
        },
    )

    client.post(
        "/users",
        json={
            "name": "Cliente Dois",
            "email": "cliente2@example.com",
            "password": "senha123",
        },
    )

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

    category_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    category_id = category_response.json()["id"]

    customer_one_token = login_user(client, "cliente1@example.com")
    customer_two_token = login_user(client, "cliente2@example.com")

    ticket_response = client.post(
        "/tickets",
        json={
            "title": "Notebook não liga",
            "description": "O notebook não apresenta nenhum sinal de energia.",
            "priority": "high",
            "category_id": category_id,
        },
        headers={
            "Authorization": f"Bearer {customer_one_token}",
        },
    )

    assert ticket_response.status_code == 201

    ticket_id = ticket_response.json()["id"]

    response = client.get(
        f"/tickets/{ticket_id}",
        headers={
            "Authorization": f"Bearer {customer_two_token}",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


def test_ticket_status_workflow(client, db):
    client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

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

    category_response = client.post(
        "/categories",
        json={
            "name": "Hardware",
            "description": "Problemas de hardware",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    category_id = category_response.json()["id"]

    customer_token = login_user(client, "cliente@example.com")

    ticket_response = client.post(
        "/tickets",
        json={
            "title": "Problema no computador",
            "description": "O computador apresenta falha durante a inicialização.",
            "priority": "high",
            "category_id": category_id,
        },
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    ticket_id = ticket_response.json()["id"]

    assign_response = client.patch(
        f"/tickets/{ticket_id}/assign",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert assign_response.status_code == 200
    assert assign_response.json()["status"] == "in_progress"

    resolved_response = client.patch(
        f"/tickets/{ticket_id}/status",
        json={
            "status": "resolved",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert resolved_response.status_code == 200
    assert resolved_response.json()["status"] == "resolved"
    assert resolved_response.json()["closed_at"] is None

    closed_response = client.patch(
        f"/tickets/{ticket_id}/status",
        json={
            "status": "closed",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert closed_response.status_code == 200
    assert closed_response.json()["status"] == "closed"
    assert closed_response.json()["closed_at"] is not None

    reopen_response = client.patch(
        f"/tickets/{ticket_id}/status",
        json={
            "status": "in_progress",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert reopen_response.status_code == 400
    assert reopen_response.json() == {
        "detail": "Cannot change ticket status from closed to in_progress"
    }
