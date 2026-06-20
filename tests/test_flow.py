from datetime import datetime, timedelta, timezone


def _register(client, email):
    response = client.post(
        "/users",
        json={
            "email": email,
            "password": "password123",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_header(client, email):
    response = client.post(
        "/auth/login",
        data={"username": email, "password": "password123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_flow(client, db_conn, address_id):
    # 1. Rejestracja uczestnika - domyślny status to 'nieaktywowany'.
    attendee = _register(client, "attendee@example.com")
    assert attendee["status"] == "nieaktywowany"

    # 2. Rejestracja moderatora i bootstrap przez bezpośredni SQL (jak w README).
    moderator = _register(client, "moderator@example.com")
    cursor = db_conn.cursor()
    cursor.execute(
        "UPDATE users SET status = 'moderator' WHERE id = %s;",
        (moderator["id"],),
    )

    # 3. Logowanie moderatora.
    mod_headers = _auth_header(client, "moderator@example.com")

    # 4. Moderator aktywuje uczestnika.
    response = client.patch(
        f"/users/{attendee['id']}",
        json={"status": "zwykły"},
        headers=mod_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "zwykły"

    # 5. Logowanie aktywowanego uczestnika (zostaje właścicielem wydarzenia).
    owner_headers = _auth_header(client, "attendee@example.com")

    # 6. Tworzenie, zgłoszenie i akceptacja wydarzenia.
    response = client.post(
        "/events",
        json={
            "title": "Flow Test Event",
            "description": "An event created by the flow test.",
            "public": True,
            "participant_limit": 100,
            "social_media_links": "",
        },
        headers=owner_headers,
    )
    assert response.status_code == 201, response.text
    event = response.json()
    assert event["status"] == "szkic"
    event_id = event["id"]

    response = client.post(f"/events/{event_id}/submit", headers=owner_headers)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "oczekujace_na_akceptacje"

    response = client.post(f"/events/{event_id}/approve", headers=mod_headers)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "zaakceptowane"

    # 7. Moderator tworzy lokację (typ 'wlasne' pomija sprawdzanie dostępności sali).
    response = client.post(
        "/locations",
        json={
            "name": "Flow Test Venue",
            "address_id": address_id,
            "type": "wlasne",
            "capacity": None,
            "is_active": True,
        },
        headers=mod_headers,
    )
    assert response.status_code == 201, response.text
    location_id = response.json()["id"]

    # 8. Właściciel tworzy wystąpienie wydarzenia, automatycznie zostaje organizatorem.
    start = datetime.now(timezone.utc) + timedelta(days=7)
    end = start + timedelta(hours=2)
    response = client.post(
        f"/events/{event_id}/occurrences",
        json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "location_id": location_id,
        },
        headers=owner_headers,
    )
    assert response.status_code == 201, response.text
    occurrence = response.json()
    assert occurrence["status"] == "zaplanowane"
    occurrence_id = occurrence["id"]

    cursor.execute(
        """
        SELECT status FROM event_registrations
        WHERE occurrence_id = %s AND user_id = %s;
        """,
        (occurrence_id, attendee["id"]),
    )
    assert cursor.fetchone()["status"] == "organizator"

    second = _register(client, "second@example.com")
    cursor.execute(
        "UPDATE users SET status = 'zwykły' WHERE id = %s;",
        (second["id"],),
    )
    second_headers = _auth_header(client, "second@example.com")

    response = client.post(
        f"/occurrences/{occurrence_id}/registrations",
        headers=second_headers,
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "zapisany"

    response = client.get(f"/events/{event_id}", headers=owner_headers)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == event_id

    response = client.get(f"/occurrences/{occurrence_id}", headers=owner_headers)
    assert response.status_code == 200, response.text
    assert response.json()["id"] == occurrence_id

    response = client.get(
        f"/occurrences/{occurrence_id}/registrations",
        headers=owner_headers,
    )
    assert response.status_code == 200, response.text
    statuses = sorted(r["status"] for r in response.json())
    assert statuses == ["organizator", "zapisany"]
