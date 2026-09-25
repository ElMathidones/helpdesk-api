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


def test_customer_can_create_and_list_comments(client, db):
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

    comment_response = client.post(
        f"/tickets/{ticket_id}/comments",
        json={
            "content": "Olá! Estou verificando o seu chamado.",
        },
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    assert comment_response.status_code == 201

    comment_data = comment_response.json()

    assert comment_data["ticket_id"] == ticket_id
    assert comment_data["author_id"] == (
        db.query(User).filter(User.email == "cliente@example.com").first().id
    )
    assert comment_data["content"] == "Olá! Estou verificando o seu chamado."
    assert comment_data["created_at"] is not None

    comments_response = client.get(
        f"/tickets/{ticket_id}/comments",
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    assert comments_response.status_code == 200

    comments_data = comments_response.json()

    assert len(comments_data) == 1
    assert comments_data[0]["id"] == comment_data["id"]
    assert comments_data[0]["content"] == "Olá! Estou verificando o seu chamado."


def test_customer_cannot_access_comments_from_another_customer(
    client,
    db,
):
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
    customer_one_token = login_user(client, "cliente1@example.com")
    customer_two_token = login_user(client, "cliente2@example.com")

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

    ticket_response = client.post(
        "/tickets",
        json={
            "title": "Computador não liga",
            "description": "O computador não apresenta nenhum sinal.",
            "priority": "high",
            "category_id": category_id,
        },
        headers={
            "Authorization": f"Bearer {customer_one_token}",
        },
    )

    assert ticket_response.status_code == 201

    ticket_id = ticket_response.json()["id"]

    comment_response = client.post(
        f"/tickets/{ticket_id}/comments",
        json={
            "content": "Mensagem privada do chamado.",
        },
        headers={
            "Authorization": f"Bearer {customer_one_token}",
        },
    )

    assert comment_response.status_code == 201

    response = client.get(
        f"/tickets/{ticket_id}/comments",
        headers={
            "Authorization": f"Bearer {customer_two_token}",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


def test_admin_can_access_comments_from_another_customer(
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
    customer_token = login_user(client, "cliente@example.com")

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

    comment_response = client.post(
        f"/tickets/{ticket_id}/comments",
        json={
            "content": "Comentário do cliente.",
        },
        headers={
            "Authorization": f"Bearer {customer_token}",
        },
    )

    assert comment_response.status_code == 201

    response = client.get(
        f"/tickets/{ticket_id}/comments",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200

    comments = response.json()

    assert len(comments) == 1
    assert comments[0]["content"] == "Comentário do cliente."
