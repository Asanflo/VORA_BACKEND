import pytest

@pytest.mark.asyncio
async def test_negotiation_counter_offer_and_acceptance(client):
    # Connexion Passager et Chauffeur
    resp_p = await client.post("/api/v1/auth/verify-otp", json={"phone_number": "+237699112233", "otp_code": "1234"})
    p_headers = {"Authorization": f"Bearer {resp_p.json()['access_token']}"}

    resp_d = await client.post("/api/v1/auth/verify-otp", json={"phone_number": "+237677445566", "otp_code": "1234"})
    d_headers = {"Authorization": f"Bearer {resp_d.json()['access_token']}"}

    # Passager crée une course avec prix initial de 1200 FCFA
    create_resp = await client.post(
        "/api/v1/rides",
        headers=p_headers,
        json={
            "pickup_name": "Total Melen",
            "dropoff_name": "Carrefour Nlongkak",
            "pickup_lat": 3.8512,
            "pickup_lng": 11.4981,
            "dropoff_lat": 3.8821,
            "dropoff_lng": 11.5234,
            "payment_mode": "MOMO",
            "ride_type": "SOLO",
            "proposed_price": 1200.0
        }
    )
    ride_id = create_resp.json()["id"]

    # Le chauffeur fait une contre-offre à 1500 FCFA
    offer_resp = await client.post(
        f"/api/v1/rides/{ride_id}/negotiation/offer",
        headers=d_headers,
        json={"offered_price": 1500.0, "driver_eta_minutes": 7}
    )
    assert offer_resp.status_code == 200
    offer_id = offer_resp.json()["id"]
    assert offer_resp.json()["offered_price"] == 1500.0

    # Le passager consulte la liste des offres reçues
    offers_list = await client.get(f"/api/v1/rides/{ride_id}/negotiation/offers", headers=p_headers)
    assert offers_list.status_code == 200
    assert len(offers_list.json()) >= 1

    # Le passager accepte la contre-offre du chauffeur
    accept_resp = await client.post(
        f"/api/v1/rides/{ride_id}/negotiation/offers/{offer_id}/accept",
        headers=p_headers
    )
    assert accept_resp.status_code == 200
    ride_updated = accept_resp.json()
    assert ride_updated["agreed_price"] == 1500.0
    assert ride_updated["status"] == "ACCEPTED"
