import uuid


def test_register_user_succeeds(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        "/register",
        json={"email": email, "password": "senha123", "role": "organizer"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Usuário criado com sucesso"}


def test_register_duplicate_email_fails(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    payload = {"email": email, "password": "senha123", "role": "client"}

    first = client.post("/register", json=payload)
    second = client.post("/register", json=payload)

    assert first.status_code == 200
    assert second.status_code == 400
    assert "já está cadastrado" in second.json()["detail"]


def test_login_with_correct_credentials_returns_token(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/register", json={"email": email, "password": "senha123", "role": "client"})

    response = client.post("/token", data={"username": email, "password": "senha123"})

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_with_wrong_password_fails(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    client.post("/register", json={"email": email, "password": "senha123", "role": "client"})

    response = client.post("/token", data={"username": email, "password": "senha_errada"})

    assert response.status_code == 401


def test_login_with_unknown_email_fails(client):
    response = client.post(
        "/token", data={"username": "nao_existe@example.com", "password": "qualquer"}
    )
    assert response.status_code == 401