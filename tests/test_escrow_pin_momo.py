import pytest

@pytest.mark.asyncio
async def test_full_momo_escrow_and_oral_pin_workflow(client):
    # 1. Connexion du passager de démo
    resp_p = await client.post("/api/v1/auth/verify-otp", json={
        "phone_number": "+237699112233",
        "otp_code": "1234"
    })
    passenger_token = resp_p.json()["access_token"]
    passenger_headers = {"Authorization": f"Bearer {passenger_token}"}

    # 2. Connexion du chauffeur de démo vérifié (+237677445566)
    resp_d = await client.post("/api/v1/auth/verify-otp", json={
        "phone_number": "+237677445566",
        "otp_code": "1234"
    })
    driver_token = resp_d.json()["access_token"]
    driver_headers = {"Authorization": f"Bearer {driver_token}"}

    # 3. Le passager réserve la course en mode Mobile Money (Séquestre)
    create_resp = await client.post(
        "/api/v1/rides",
        headers=passenger_headers,
        json={
            "pickup_name": "Carrefour EMIA",
            "dropoff_name": "Marché Mokolo",
            "pickup_lat": 3.8568,
            "pickup_lng": 11.5015,
            "dropoff_lat": 3.8741,
            "dropoff_lng": 11.5032,
            "payment_mode": "MOMO",
            "ride_type": "SOLO",
            "proposed_price": 1500.0
        }
    )
    assert create_resp.status_code == 201
    ride_data = create_resp.json()
    ride_id = ride_data["id"]
    secret_pin = ride_data["secret_pin"]
    assert secret_pin is not None
    assert len(secret_pin) == 4
    assert ride_data["status"] == "REQUESTED"
    assert ride_data["is_locked"] is False

    # Vérification du séquestre (Fonds gelés chez l'agrégateur)
    escrow_resp = await client.get(f"/api/v1/escrow/ride/{ride_id}", headers=passenger_headers)
    assert escrow_resp.status_code == 200
    assert escrow_resp.json()["status"] == "HELD"
    assert escrow_resp.json()["amount"] == 1500.0

    # 4. Le chauffeur accepte la course
    accept_resp = await client.post(f"/api/v1/rides/{ride_id}/accept", headers=driver_headers)
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "ACCEPTED"

    # 5. Le chauffeur démarre la course (Verrouillage absolu)
    start_resp = await client.post(f"/api/v1/rides/{ride_id}/start", headers=driver_headers)
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "STARTED"
    assert start_resp.json()["is_locked"] is True

    # 6. RÈGLE D'ARRÊT : Le passager tente d'annuler -> DOIT ÊTRE REJETÉ !
    cancel_resp = await client.post(f"/api/v1/rides/{ride_id}/cancel", headers=passenger_headers)
    assert cancel_resp.status_code == 400
    assert "verrouillée" in cancel_resp.json()["detail"].lower()

    # 7. Tentative avec un mauvais code PIN par le chauffeur
    bad_pin_resp = await client.post(
        f"/api/v1/rides/{ride_id}/complete-with-pin",
        headers=driver_headers,
        json={"pin": "0000"}
    )
    assert bad_pin_resp.status_code == 400
    assert "incorrect" in bad_pin_resp.json()["detail"].lower()

    # 8. Saisie du BON code PIN oral dicté par le passager à destination
    good_pin_resp = await client.post(
        f"/api/v1/rides/{ride_id}/complete-with-pin",
        headers=driver_headers,
        json={"pin": secret_pin}
    )
    assert good_pin_resp.status_code == 200
    assert good_pin_resp.json()["status"] == "COMPLETED"

    # 9. Vérification finale : Les fonds du séquestre sont libérés vers le chauffeur
    escrow_final = await client.get(f"/api/v1/escrow/ride/{ride_id}", headers=passenger_headers)
    assert escrow_final.status_code == 200
    assert escrow_final.json()["status"] == "RELEASED"
    assert escrow_final.json()["driver_net_amount"] > 0

