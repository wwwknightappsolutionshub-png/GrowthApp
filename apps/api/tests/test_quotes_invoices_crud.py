"""Quotes & invoices CRUD — available to all tenants (no accounting add-on gate)."""
from __future__ import annotations

import uuid

import pytest


async def _register(client) -> str:
    email = f"qi-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TestPass123",
            "full_name": "QI Tester",
            "business_name": f"QI Plumbing {uuid.uuid4().hex[:6]}",
            "business_type": "plumber",
            "postcode": "SW1A 1AA",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_quotes_and_invoices_full_crud(client):
    token = await _register(client)
    headers = _auth(token)

    cust = await client.post(
        "/api/v1/crm/customers",
        headers=headers,
        json={"first_name": "Jane", "last_name": "Client", "email": "jane@example.com"},
    )
    assert cust.status_code == 201, cust.text
    customer_id = cust.json()["id"]

    # Create quote
    q_create = await client.post(
        "/api/v1/quotes",
        headers=headers,
        json={
            "customer_id": customer_id,
            "title": "Bathroom refit",
            "items": [
                {
                    "description": "Labour",
                    "quantity": 1,
                    "unit_price_pence": 50000,
                    "vat_rate": 20,
                }
            ],
        },
    )
    assert q_create.status_code == 201, q_create.text
    quote = q_create.json()
    quote_id = quote["id"]
    assert quote["quote_number"].startswith("QT-")
    assert quote["total_pence"] == 60000  # 50000 + 20% VAT
    assert quote["status"] == "draft"

    # Update quote
    q_patch = await client.patch(
        f"/api/v1/quotes/{quote_id}",
        headers=headers,
        json={"title": "Bathroom refit (revised)", "items": [{"description": "Labour", "quantity": 2, "unit_price_pence": 25000, "vat_rate": 20}]},
    )
    assert q_patch.status_code == 200, q_patch.text
    assert q_patch.json()["title"] == "Bathroom refit (revised)"
    assert q_patch.json()["total_pence"] == 60000

    # List quotes
    q_list = await client.get("/api/v1/quotes", headers=headers)
    assert q_list.status_code == 200
    assert q_list.json()["total"] >= 1

    # Create invoice
    inv_create = await client.post(
        "/api/v1/invoices",
        headers=headers,
        json={
            "customer_id": customer_id,
            "title": "Deposit invoice",
            "due_date": "2026-12-31",
            "items": [{"description": "Deposit", "quantity": 1, "unit_price_pence": 10000, "vat_rate": 20}],
        },
    )
    assert inv_create.status_code == 201, inv_create.text
    invoice = inv_create.json()
    invoice_id = invoice["id"]
    assert invoice["invoice_number"].startswith("INV-")
    assert invoice["status"] == "draft"
    assert invoice["total_pence"] == 12000

    # Update invoice
    inv_patch = await client.patch(
        f"/api/v1/invoices/{invoice_id}",
        headers=headers,
        json={"title": "Deposit invoice (updated)"},
    )
    assert inv_patch.status_code == 200, inv_patch.text
    assert inv_patch.json()["title"] == "Deposit invoice (updated)"

    # Delete invoice (draft)
    inv_del = await client.delete(f"/api/v1/invoices/{invoice_id}", headers=headers)
    assert inv_del.status_code == 204

    inv_get = await client.get(f"/api/v1/invoices/{invoice_id}", headers=headers)
    assert inv_get.status_code == 404

    # Delete quote (draft)
    q_del = await client.delete(f"/api/v1/quotes/{quote_id}", headers=headers)
    assert q_del.status_code == 204

    q_get = await client.get(f"/api/v1/quotes/{quote_id}", headers=headers)
    assert q_get.status_code == 404


@pytest.mark.asyncio
async def test_cannot_delete_sent_quote(client):
    token = await _register(client)
    headers = _auth(token)

    cust = await client.post(
        "/api/v1/crm/customers",
        headers=headers,
        json={"first_name": "Bob", "last_name": "X"},
    )
    customer_id = cust.json()["id"]

    q = await client.post(
        "/api/v1/quotes",
        headers=headers,
        json={
            "customer_id": customer_id,
            "title": "Small job",
            "items": [{"description": "Work", "quantity": 1, "unit_price_pence": 1000, "vat_rate": 20}],
        },
    )
    quote_id = q.json()["id"]
    send = await client.post(f"/api/v1/quotes/{quote_id}/send", headers=headers)
    assert send.status_code == 200

    bad = await client.delete(f"/api/v1/quotes/{quote_id}", headers=headers)
    assert bad.status_code == 400
