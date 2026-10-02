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

    history_response = client.get(
        f"/tickets/{data['id']}/history",
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 1
    assert history[0]["event_type"] == "ticket_created"
    assert history[0]["old_value"] is None
    assert history[0]["new_value"] is None
    assert history[0]["user"]["name"] == "Cliente Teste"


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

    history_response = client.get(
        f"/tickets/{ticket_id}/history",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 3

    assert history[0]["event_type"] == "ticket_created"

    assert history[1]["event_type"] == "assignee_changed"
    assert history[1]["old_value"] is None
    assert history[1]["new_value"] == str(admin.id)
    assert history[1]["user"]["name"] == "Admin Teste"

    assert history[2]["event_type"] == "status_changed"
    assert history[2]["old_value"] == "open"
    assert history[2]["new_value"] == "in_progress"
    assert history[2]["user"]["name"] == "Admin Teste"


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

    history_response = client.get(
        f"/tickets/{ticket_id}/history",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 5

    assert history[3]["event_type"] == "status_changed"
    assert history[3]["old_value"] == "in_progress"
    assert history[3]["new_value"] == "resolved"
    assert history[3]["user"]["name"] == "Admin Teste"

    assert history[4]["event_type"] == "status_changed"
    assert history[4]["old_value"] == "resolved"
    assert history[4]["new_value"] == "closed"
    assert history[4]["user"]["name"] == "Admin Teste"

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


def test_create_ticket_with_unknown_category_returns_400(client):
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
        "/tickets",
        json={
            "title": "Problema no computador",
            "description": "O computador apresenta um problema durante o uso.",
            "priority": "medium",
            "category_id": 99999,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Category not found"}


def test_customer_cannot_update_ticket_status(client, db):
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
            "title": "Problema de hardware",
            "description": "O computador está apresentando falhas de hardware.",
            "priority": "high",
            "category_id": category_id,
        },
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    ticket_id = ticket_response.json()["id"]

    response = client.patch(
        f"/tickets/{ticket_id}/status",
        json={
            "status": "resolved",
        },
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


def test_assign_unknown_ticket_returns_400(client, db):
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
        "/tickets/99999/assign",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Ticket not found"}


def test_invalid_ticket_status_transition_returns_400(client, db):
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
            "title": "Computador com defeito",
            "description": "O computador apresenta falhas durante a inicialização.",
            "priority": "medium",
            "category_id": category_id,
        },
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    ticket_id = ticket_response.json()["id"]

    response = client.patch(
        f"/tickets/{ticket_id}/status",
        json={
            "status": "closed",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Cannot change ticket status from open to closed"
    }


def test_cannot_create_ticket_with_inactive_category(client, db):
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

    deactivate_response = client.patch(
        f"/categories/{category_id}/status",
        json={
            "is_active": False,
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    customer_token = login_user(client, "cliente@example.com")

    response = client.post(
        "/tickets",
        json={
            "title": "Problema de hardware",
            "description": "O computador apresenta falha de hardware.",
            "priority": "high",
            "category_id": category_id,
        },
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Category is inactive",
    }


def test_existing_ticket_remains_accessible_after_category_is_deactivated(
    client,
    db,
):
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

    ticket_response = client.post(
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

    assert ticket_response.status_code == 201

    ticket_id = ticket_response.json()["id"]

    deactivate_response = client.patch(
        f"/categories/{category_id}/status",
        json={
            "is_active": False,
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert deactivate_response.status_code == 200

    response = client.get(
        f"/tickets/{ticket_id}",
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == ticket_id
    assert data["category_id"] == category_id
