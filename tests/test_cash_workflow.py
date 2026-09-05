import pytest

@pytest.mark.asyncio
async def test_cash_payment_workflow_and_lock(client):
    # 1. Connexion Passager et Chauffeur
    resp_p = await client.post("/api/v1/auth/verify-otp", json={
        "phone_number": "+237699112233",
        "otp_code": "1234"
    })
    p_token = resp_p.json()["access_token"]
    p_headers = {"Authorization": f"Bearer {p_token}"}

    resp_d = await client.post("/api/v1/auth/verify-otp", json={
        "phone_number": "+237677445566",
        "otp_code": "1234"
    })
    d_token = resp_d.json()["access_token"]
    d_headers = {"Authorization": f"Bearer {d_token}"}

    # 2. Passager sélectionne le mode "Espèces" (Cash)
    create_resp = await client.post(
        "/api/v1/rides",
        headers=p_headers,
        json={
            "pickup_name": "Poste Centrale",
            "dropoff_name": "Carrefour Bastos",
            "pickup_lat": 3.8667,
            "pickup_lng": 11.5198,
            "dropoff_lat": 3.8950,
            "dropoff_lng": 11.5150,
            "payment_mode": "CASH",
            "ride_type": "SOLO",
            "proposed_price": 2000.0
        }
    )
    assert create_resp.status_code == 201
    ride_id = create_resp.json()["id"]
    assert create_resp.json()["payment_mode"] == "CASH"

    # Pas de séquestre en mode espèces
    escrow_resp = await client.get(f"/api/v1/escrow/ride/{ride_id}", headers=p_headers)
    assert escrow_resp.status_code == 404

    # 3. Chauffeur accepte la course
    accept_resp = await client.post(f"/api/v1/rides/{ride_id}/accept", headers=d_headers)
    assert accept_resp.status_code == 200

    # 4. Chauffeur démarre la course (Verrouillage absolu)
    start_resp = await client.post(f"/api/v1/rides/{ride_id}/start", headers=d_headers)
    assert start_resp.status_code == 200
    assert start_resp.json()["is_locked"] is True

    # 5. Tentative d'annulation -> Interdite
    cancel_resp = await client.post(f"/api/v1/rides/{ride_id}/cancel", headers=p_headers)
    assert cancel_resp.status_code == 400
    assert "verrouillée" in cancel_resp.json()["detail"].lower()

    # 6. Arrivée à destination : Chauffeur valide simplement la fin de course (pas de code PIN)
    complete_resp = await client.post(f"/api/v1/rides/{ride_id}/complete-cash", headers=d_headers)
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "COMPLETED"
    assert "commission" in complete_resp.json()["message"].lower()

