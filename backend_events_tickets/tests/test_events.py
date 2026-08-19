def _event_payload(title="Evento Teste"):
    return {
        "title": title,
        "location": "Arena Teste",
        "date": "2026-12-01",
        "price": 100.0,
    }


def test_organizer_can_create_event(client, auth_headers):
    headers = auth_headers("organizer")

    response = client.post("/events", json=_event_payload(), headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Evento Teste"
    assert "organizer_id" in body
    assert "id" in body


def test_client_cannot_create_event(client, auth_headers):
    headers = auth_headers("client")

    response = client.post("/events", json=_event_payload(), headers=headers)

    assert response.status_code == 403


def test_gate_cannot_create_event(client, auth_headers):
    headers = auth_headers("gate")

    response = client.post("/events", json=_event_payload(), headers=headers)

    assert response.status_code == 403


def test_create_event_requires_authentication(client):
    response = client.post("/events", json=_event_payload())

    assert response.status_code == 401