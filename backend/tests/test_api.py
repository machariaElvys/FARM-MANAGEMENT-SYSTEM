"""API tests: auth, ownership isolation, reports (profit/monthly/CSV), rate limits, admin, sync."""

import uuid

from conftest import auth_headers, register


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_login_and_me(client):
    session = register(client)
    assert session["user"]["role"] == "farmer"
    assert session["token_type"] == "bearer"

    me = client.get("/api/auth/me", headers=auth_headers(session["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "farmer@example.com"

    login = client.post("/api/auth/login", json={"email": "farmer@example.com", "password": "password123"})
    assert login.status_code == 200

    wrong = client.post("/api/auth/login", json={"email": "farmer@example.com", "password": "wrong-password"})
    assert wrong.status_code == 401


def test_duplicate_email_conflict(client):
    register(client)
    response = client.post(
        "/api/auth/register",
        json={"name": "Other", "email": "FARMER@example.com", "password": "password123"},
    )
    assert response.status_code == 409


def test_records_require_auth(client):
    assert client.get("/api/records").status_code == 401
    assert client.get("/api/reports/summary").status_code == 401


def test_record_crud_and_ownership_isolation(client):
    owner = register(client, email="owner@example.com")
    other = register(client, email="other@example.com")
    owner_headers = auth_headers(owner["access_token"])
    other_headers = auth_headers(other["access_token"])

    created = client.post(
        "/api/records",
        headers=owner_headers,
        json={"title": "Bought fertilizer", "category": "inputs", "occurred_on": "2026-03-01", "amount": "5000"},
    )
    assert created.status_code == 201, created.text
    record_id = created.json()["id"]

    # Other farmer cannot see, edit, or delete it.
    assert client.get("/api/records", headers=other_headers).json() == []
    assert (
        client.put(
            f"/api/records/{record_id}",
            headers=other_headers,
            json={"title": "Hijacked", "category": "inputs", "occurred_on": "2026-03-02"},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/records/{record_id}", headers=other_headers).status_code == 404

    # Owner can update and delete.
    updated = client.put(
        f"/api/records/{record_id}",
        headers=owner_headers,
        json={"title": "Bought fertilizer (updated)", "category": "inputs", "occurred_on": "2026-03-01", "amount": "5500"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Bought fertilizer (updated)"
    assert client.delete(f"/api/records/{record_id}", headers=owner_headers).status_code == 204


def test_report_profit_and_monthly(client):
    session = register(client)
    headers = auth_headers(session["access_token"])
    for payload in [
        {"title": "Fertilizer", "category": "inputs", "occurred_on": "2026-03-01", "amount": "5000"},
        {"title": "Labour", "category": "labour", "occurred_on": "2026-03-05", "amount": "3000"},
        {"title": "Maize sale", "category": "sales", "occurred_on": "2026-03-10", "amount": "20000"},
        {"title": "Maize harvest", "category": "harvest", "occurred_on": "2026-03-12", "quantity": "40", "unit": "bags"},
    ]:
        assert client.post("/api/records", headers=headers, json=payload).status_code == 201

    report = client.get("/api/reports/summary?year=2026", headers=headers)
    assert report.status_code == 200
    data = report.json()
    assert data["expenses"] == 8000
    assert data["sales"] == 20000
    assert data["profit"] == 12000
    assert data["record_count"] == 4
    assert data["harvest_quantities"] == [{"unit": "bags", "quantity": 40.0}]
    assert len(data["monthly"]) == 12
    march = data["monthly"][2]
    assert march["label"] == "Mar"
    assert march["profit"] == 12000
    assert march["record_count"] == 4


def test_csv_export(client):
    session = register(client)
    headers = auth_headers(session["access_token"])
    client.post(
        "/api/records",
        headers=headers,
        json={"title": "Fertilizer", "category": "inputs", "occurred_on": "2026-03-01", "amount": "5000"},
    )
    response = client.get("/api/reports/export.csv?year=2026", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    body = response.text
    assert body.startswith("date,category,title,quantity,unit,amount_kes,notes")
    assert "Fertilizer" in body
    assert "5000" in body


def test_login_rate_limit(client):
    register(client)
    for _ in range(10):
        client.post("/api/auth/login", json={"email": "farmer@example.com", "password": "wrong-password"})
    response = client.post("/api/auth/login", json={"email": "farmer@example.com", "password": "wrong-password"})
    assert response.status_code == 429
    assert response.headers.get("retry-after") == "60"


def test_admin_endpoints_require_admin(client):
    session = register(client)
    headers = auth_headers(session["access_token"])
    assert client.get("/api/admin/overview", headers=headers).status_code == 403
    assert client.get("/api/admin/users", headers=headers).status_code == 403


def test_sync_upsert_and_delete(client):
    session = register(client)
    headers = auth_headers(session["access_token"])
    record_id = str(uuid.uuid4())
    operation_id = str(uuid.uuid4())

    synced = client.post(
        "/api/records/sync",
        headers=headers,
        json={
            "operations": [
                {
                    "operation_id": operation_id,
                    "action": "upsert",
                    "record_id": record_id,
                    "record": {
                        "id": record_id,
                        "title": "Offline entry",
                        "category": "planting",
                        "occurred_on": "2026-04-01",
                    },
                }
            ]
        },
    )
    assert synced.status_code == 200, synced.text
    assert synced.json()["results"][0]["action"] == "upsert"
    assert len(client.get("/api/records", headers=headers).json()) == 1

    deleted = client.post(
        "/api/records/sync",
        headers=headers,
        json={"operations": [{"operation_id": str(uuid.uuid4()), "action": "delete", "record_id": record_id}]},
    )
    assert deleted.status_code == 200
    assert client.get("/api/records", headers=headers).json() == []
