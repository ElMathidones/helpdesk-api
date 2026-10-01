from datetime import UTC, datetime

from app.models.category import Category
from app.models.ticket import Ticket
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


def make_user_admin(db, user_id: int) -> None:
    user = db.get(User, user_id)
    user.role = "admin"
    db.commit()


def test_report_summary_requires_authentication(client):
    response = client.get("/reports/summary")

    assert response.status_code == 401


def test_authenticated_user_can_get_report_summary(client, db):
    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    assert user_response.status_code == 201

    user_id = user_response.json()["id"]
    make_user_admin(db, user_id)

    token = login_user(client, "usuario@example.com")

    response = client.get(
        "/reports/summary",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    assert response.json() == {
        "total": 0,
        "open": 0,
        "in_progress": 0,
        "resolved": 0,
        "canceled": 0,
    }


def test_report_summary_rejects_invalid_date_range(client, db):
    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    user_id = user_response.json()["id"]
    make_user_admin(db, user_id)

    token = login_user(client, "usuario@example.com")

    response = client.get(
        "/reports/summary",
        params={
            "start_date": "2026-10-20",
            "end_date": "2026-10-01",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "A data inicial não pode ser posterior à data final."
    }


def test_report_summary_filters_tickets_by_date(client, db):
    from app.models.category import Category
    from app.models.ticket import Ticket

    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    user_id = user_response.json()["id"]
    make_user_admin(db, user_id)

    token = login_user(client, "usuario@example.com")

    category = Category(
        name="Hardware",
        description="Problemas de hardware",
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    ticket = Ticket(
        title="Computador não liga",
        description="O computador não apresenta nenhum sinal.",
        priority="high",
        category_id=category.id,
        creator_id=user_id,
    )
    db.add(ticket)
    db.commit()

    response = client.get(
        "/reports/summary",
        params={
            "start_date": "2030-01-01",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_report_timeline_requires_authentication(client):
    response = client.get("/reports/timeline")

    assert response.status_code == 401


def test_report_timeline_groups_tickets_by_date(client, db):
    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    user_id = user_response.json()["id"]
    make_user_admin(db, user_id)

    token = login_user(client, "usuario@example.com")

    category = Category(
        name="Hardware",
        description="Problemas de hardware",
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    first_ticket = Ticket(
        title="Primeiro chamado",
        description="Primeiro chamado do teste.",
        priority="medium",
        category_id=category.id,
        creator_id=user_id,
        created_at=datetime(2026, 9, 15, 8, 30, tzinfo=UTC),
    )

    second_ticket = Ticket(
        title="Segundo chamado",
        description="Segundo chamado do teste.",
        priority="high",
        category_id=category.id,
        creator_id=user_id,
        created_at=datetime(2026, 9, 15, 16, 45, tzinfo=UTC),
    )

    db.add_all([first_ticket, second_ticket])
    db.commit()

    response = client.get(
        "/reports/timeline",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "date": "2026-09-15",
            "created": 2,
        }
    ]


def test_report_timeline_filters_by_date_range(client, db):
    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    user_id = user_response.json()["id"]
    make_user_admin(db, user_id)

    token = login_user(client, "usuario@example.com")

    category = Category(
        name="Hardware",
        description="Problemas de hardware",
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    tickets = [
        Ticket(
            title="Chamado anterior",
            description="Fora do período.",
            priority="medium",
            category_id=category.id,
            creator_id=user_id,
            created_at=datetime(2026, 9, 14, 10, 0, tzinfo=UTC),
        ),
        Ticket(
            title="Chamado dentro do período",
            description="Dentro do período.",
            priority="high",
            category_id=category.id,
            creator_id=user_id,
            created_at=datetime(2026, 9, 15, 10, 0, tzinfo=UTC),
        ),
        Ticket(
            title="Chamado posterior",
            description="Fora do período.",
            priority="low",
            category_id=category.id,
            creator_id=user_id,
            created_at=datetime(2026, 9, 18, 10, 0, tzinfo=UTC),
        ),
    ]

    db.add_all(tickets)
    db.commit()

    response = client.get(
        "/reports/timeline",
        params={
            "start_date": "2026-09-15",
            "end_date": "2026-09-17",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "date": "2026-09-15",
            "created": 1,
        }
    ]


def test_report_priority_distribution_requires_authentication(client):
    response = client.get("/reports/by-priority")

    assert response.status_code == 401


def test_report_priority_distribution_groups_tickets_by_priority(client, db):
    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    user_id = user_response.json()["id"]
    make_user_admin(db, user_id)

    token = login_user(client, "usuario@example.com")

    category = Category(
        name="Hardware",
        description="Problemas de hardware",
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    tickets = [
        Ticket(
            title="Chamado baixo",
            description="Chamado de prioridade baixa.",
            priority="low",
            category_id=category.id,
            creator_id=user_id,
        ),
        Ticket(
            title="Chamado alto 1",
            description="Primeiro chamado de prioridade alta.",
            priority="high",
            category_id=category.id,
            creator_id=user_id,
        ),
        Ticket(
            title="Chamado alto 2",
            description="Segundo chamado de prioridade alta.",
            priority="high",
            category_id=category.id,
            creator_id=user_id,
        ),
    ]

    db.add_all(tickets)
    db.commit()

    response = client.get(
        "/reports/by-priority",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 2

    distribution = {item["priority"]: item["count"] for item in data}

    assert distribution == {
        "low": 1,
        "high": 2,
    }


def test_report_priority_distribution_filters_by_date_range(client, db):
    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    user_id = user_response.json()["id"]
    make_user_admin(db, user_id)

    token = login_user(client, "usuario@example.com")

    category = Category(
        name="Hardware",
        description="Problemas de hardware",
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    tickets = [
        Ticket(
            title="Chamado fora do período",
            description="Este chamado não deve entrar no relatório.",
            priority="critical",
            category_id=category.id,
            creator_id=user_id,
            created_at=datetime(2026, 9, 14, 10, 0, tzinfo=UTC),
        ),
        Ticket(
            title="Chamado dentro do período",
            description="Este chamado deve entrar no relatório.",
            priority="high",
            category_id=category.id,
            creator_id=user_id,
            created_at=datetime(2026, 9, 15, 10, 0, tzinfo=UTC),
        ),
    ]

    db.add_all(tickets)
    db.commit()

    response = client.get(
        "/reports/by-priority",
        params={
            "start_date": "2026-09-15",
            "end_date": "2026-09-17",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "priority": "high",
            "count": 1,
        }
    ]


def test_report_category_distribution_requires_authentication(client):
    response = client.get("/reports/by-category")

    assert response.status_code == 401


def test_report_category_distribution_groups_tickets_by_category(client, db):
    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    user_id = user_response.json()["id"]
    make_user_admin(db, user_id)

    token = login_user(client, "usuario@example.com")

    hardware = Category(
        name="Hardware",
        description="Problemas de hardware",
    )
    network = Category(
        name="Rede",
        description="Problemas de rede",
    )

    db.add_all([hardware, network])
    db.commit()
    db.refresh(hardware)
    db.refresh(network)

    tickets = [
        Ticket(
            title="Problema de hardware 1",
            description="Primeiro problema de hardware.",
            priority="medium",
            category_id=hardware.id,
            creator_id=user_id,
        ),
        Ticket(
            title="Problema de hardware 2",
            description="Segundo problema de hardware.",
            priority="high",
            category_id=hardware.id,
            creator_id=user_id,
        ),
        Ticket(
            title="Problema de rede",
            description="Problema de conexão.",
            priority="medium",
            category_id=network.id,
            creator_id=user_id,
        ),
    ]

    db.add_all(tickets)
    db.commit()

    response = client.get(
        "/reports/by-category",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    distribution = {item["category_name"]: item["count"] for item in data}

    assert distribution == {
        "Hardware": 2,
        "Rede": 1,
    }


def test_report_category_distribution_filters_by_date_range(client, db):
    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    user_id = user_response.json()["id"]
    make_user_admin(db, user_id)

    token = login_user(client, "usuario@example.com")

    hardware = Category(
        name="Hardware",
        description="Problemas de hardware",
    )
    network = Category(
        name="Rede",
        description="Problemas de rede",
    )

    db.add_all([hardware, network])
    db.commit()
    db.refresh(hardware)
    db.refresh(network)

    tickets = [
        Ticket(
            title="Chamado fora do período",
            description="Este chamado não deve entrar no relatório.",
            priority="medium",
            category_id=network.id,
            creator_id=user_id,
            created_at=datetime(2026, 9, 14, 10, 0, tzinfo=UTC),
        ),
        Ticket(
            title="Chamado dentro do período",
            description="Este chamado deve entrar no relatório.",
            priority="high",
            category_id=hardware.id,
            creator_id=user_id,
            created_at=datetime(2026, 9, 15, 10, 0, tzinfo=UTC),
        ),
    ]

    db.add_all(tickets)
    db.commit()

    response = client.get(
        "/reports/by-category",
        params={
            "start_date": "2026-09-15",
            "end_date": "2026-09-17",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "category_id": hardware.id,
            "category_name": "Hardware",
            "count": 1,
        }
    ]


def test_report_status_distribution_requires_authentication(client):
    response = client.get("/reports/by-status")

    assert response.status_code == 401


def test_report_status_distribution_groups_tickets_by_status(client, db):
    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    user_id = user_response.json()["id"]
    make_user_admin(db, user_id)

    token = login_user(client, "usuario@example.com")

    category = Category(
        name="Hardware",
        description="Problemas de hardware",
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    tickets = [
        Ticket(
            title="Chamado aberto",
            description="Chamado que permanece aberto.",
            priority="medium",
            status="open",
            category_id=category.id,
            creator_id=user_id,
        ),
        Ticket(
            title="Chamado resolvido 1",
            description="Primeiro chamado resolvido.",
            priority="high",
            status="resolved",
            category_id=category.id,
            creator_id=user_id,
        ),
        Ticket(
            title="Chamado resolvido 2",
            description="Segundo chamado resolvido.",
            priority="high",
            status="resolved",
            category_id=category.id,
            creator_id=user_id,
        ),
    ]

    db.add_all(tickets)
    db.commit()

    response = client.get(
        "/reports/by-status",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    distribution = {item["status"]: item["count"] for item in data}

    assert distribution == {
        "open": 1,
        "resolved": 2,
    }


def test_report_status_distribution_filters_by_date_range(client, db):
    user_response = client.post(
        "/users",
        json={
            "name": "Usuário Teste",
            "email": "usuario@example.com",
            "password": "senha123",
        },
    )

    user_id = user_response.json()["id"]
    make_user_admin(db, user_id)

    token = login_user(client, "usuario@example.com")

    category = Category(
        name="Hardware",
        description="Problemas de hardware",
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    tickets = [
        Ticket(
            title="Chamado fora do período",
            description="Este chamado não deve entrar no relatório.",
            priority="medium",
            status="closed",
            category_id=category.id,
            creator_id=user_id,
            created_at=datetime(2026, 9, 14, 10, 0, tzinfo=UTC),
        ),
        Ticket(
            title="Chamado dentro do período",
            description="Este chamado deve entrar no relatório.",
            priority="high",
            status="resolved",
            category_id=category.id,
            creator_id=user_id,
            created_at=datetime(2026, 9, 15, 10, 0, tzinfo=UTC),
        ),
    ]

    db.add_all(tickets)
    db.commit()

    response = client.get(
        "/reports/by-status",
        params={
            "start_date": "2026-09-15",
            "end_date": "2026-09-17",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "status": "resolved",
            "count": 1,
        }
    ]


def test_customer_cannot_access_report_summary(client):
    client.post(
        "/users",
        json={
            "name": "Cliente Teste",
            "email": "cliente@example.com",
            "password": "senha123",
        },
    )

    token = login_user(client, "cliente@example.com")

    response = client.get(
        "/reports/summary",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permissions"}


def test_admin_can_access_report_summary(client, db):
    admin_response = client.post(
        "/users",
        json={
            "name": "Admin Teste",
            "email": "admin@example.com",
            "password": "senha123",
        },
    )

    admin_id = admin_response.json()["id"]

    admin = db.get(User, admin_id)
    admin.role = "admin"
    db.commit()

    token = login_user(client, "admin@example.com")

    response = client.get(
        "/reports/summary",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200


def test_technician_can_access_report_summary(client, db):
    technician_response = client.post(
        "/users",
        json={
            "name": "Técnico Teste",
            "email": "tecnico@example.com",
            "password": "senha123",
        },
    )

    technician_id = technician_response.json()["id"]

    technician = db.get(User, technician_id)
    technician.role = "technician"
    db.commit()

    token = login_user(client, "tecnico@example.com")

    response = client.get(
        "/reports/summary",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
