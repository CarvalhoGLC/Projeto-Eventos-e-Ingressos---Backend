def _create_event(client, auth_headers, title="Evento Bookings"):
    headers = auth_headers("organizer")
    response = client.post(
        "/events",
        json={"title": title, "location": "Local", "date": "2026-12-01", "price": 50.0},
        headers=headers,
    )
    return response.json()["id"]


def test_client_can_book_ticket(client, auth_headers):
    event_id = _create_event(client, auth_headers)
    headers = auth_headers("client")

    response = client.post(
        "/bookings",
        json={"event_id": event_id, "seat_number": "A1", "simulate_payment_success": True},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["seat"] == "A1"
    assert "qr_code_payload" in body
    assert body["share_link"].startswith("/tickets/share/")


def test_cannot_book_same_seat_twice(client, auth_headers):
    event_id = _create_event(client, auth_headers)
    headers = auth_headers("client")
    payload = {"event_id": event_id, "seat_number": "B1", "simulate_payment_success": True}

    first = client.post("/bookings", json=payload, headers=headers)
    second = client.post("/bookings", json=payload, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 400


def test_booking_fails_when_payment_declined(client, auth_headers):
    event_id = _create_event(client, auth_headers)
    headers = auth_headers("client")

    response = client.post(
        "/bookings",
        json={"event_id": event_id, "seat_number": "C1", "simulate_payment_success": False},
        headers=headers,
    )

    assert response.status_code == 400


def test_organizer_cannot_book_ticket(client, auth_headers):
    event_id = _create_event(client, auth_headers)
    headers = auth_headers("organizer")

    response = client.post(
        "/bookings",
        json={"event_id": event_id, "seat_number": "D1", "simulate_payment_success": True},
        headers=headers,
    )

    assert response.status_code == 403


def test_shared_ticket_link_returns_ticket_data(client, auth_headers):
    event_id = _create_event(client, auth_headers)
    headers = auth_headers("client")

    booking = client.post(
        "/bookings",
        json={"event_id": event_id, "seat_number": "E1", "simulate_payment_success": True},
        headers=headers,
    ).json()

    share_token = booking["share_link"].split("/")[-1]
    response = client.get(f"/tickets/share/{share_token}")

    assert response.status_code == 200
    body = response.json()
    assert body["seat_number"] == "E1"
    assert body["qr_code_payload"] == booking["qr_code_payload"]


def test_shared_ticket_with_invalid_token_returns_404(client):
    response = client.get("/tickets/share/token-que-nao-existe")

    assert response.status_code == 404