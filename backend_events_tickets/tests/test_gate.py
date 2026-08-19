def _create_event_and_ticket(client, auth_headers, seat="G1"):
    org_headers = auth_headers("organizer")
    event = client.post(
        "/events",
        json={"title": "Evento Portaria", "location": "Local", "date": "2026-12-01", "price": 80.0},
        headers=org_headers,
    ).json()

    client_headers = auth_headers("client")
    booking = client.post(
        "/bookings",
        json={"event_id": event["id"], "seat_number": seat, "simulate_payment_success": True},
        headers=client_headers,
    ).json()

    return event["id"], booking["qr_code_payload"]


def test_gate_validates_ticket_successfully(client, auth_headers):
    event_id, qr_payload = _create_event_and_ticket(client, auth_headers, seat="H1")
    headers = auth_headers("gate")

    response = client.post(
        "/gate/validate",
        params={"qr_payload": qr_payload, "gate_event_id": event_id},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "VALID"


def test_gate_rejects_ticket_used_twice(client, auth_headers):
    event_id, qr_payload = _create_event_and_ticket(client, auth_headers, seat="H2")
    headers = auth_headers("gate")
    params = {"qr_payload": qr_payload, "gate_event_id": event_id}

    first = client.post("/gate/validate", params=params, headers=headers)
    second = client.post("/gate/validate", params=params, headers=headers)

    assert first.json()["status"] == "VALID"
    assert second.json()["status"] == "USED"


def test_gate_rejects_tampered_qr_code(client, auth_headers):
    event_id, qr_payload = _create_event_and_ticket(client, auth_headers, seat="H3")
    headers = auth_headers("gate")

    # Altera o último caractere da assinatura para simular um QR Code forjado
    tampered = qr_payload[:-1] + ("0" if qr_payload[-1] != "0" else "1")

    response = client.post(
        "/gate/validate",
        params={"qr_payload": tampered, "gate_event_id": event_id},
        headers=headers,
    )

    assert response.json()["status"] == "INVALID"


def test_gate_rejects_wrong_event(client, auth_headers):
    event_id, qr_payload = _create_event_and_ticket(client, auth_headers, seat="H4")
    headers = auth_headers("gate")

    response = client.post(
        "/gate/validate",
        params={"qr_payload": qr_payload, "gate_event_id": event_id + 9999},
        headers=headers,
    )

    assert response.json()["status"] == "WRONG_EVENT"


def test_non_gate_user_cannot_validate_ticket(client, auth_headers):
    event_id, qr_payload = _create_event_and_ticket(client, auth_headers, seat="H5")
    headers = auth_headers("client")

    response = client.post(
        "/gate/validate",
        params={"qr_payload": qr_payload, "gate_event_id": event_id},
        headers=headers,
    )

    assert response.status_code == 403