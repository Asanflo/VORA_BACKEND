import pytest

@pytest.mark.asyncio
async def test_sos_trigger_and_public_live_tracking(client):
    # Connexion Passager
    resp_p = await client.post("/api/v1/auth/verify-otp", json={"phone_number": "+237699112233", "otp_code": "1234"})
    p_headers = {"Authorization": f"Bearer {resp_p.json()['access_token']}"}

    # Création de course
    ride_resp = await client.post(
        "/api/v1/rides",
        headers=p_headers,
        json={
            "pickup_name": "Carrefour Bastos",
            "dropoff_name": "Hôpital Général",
            "pickup_lat": 3.8950,
            "pickup_lng": 11.5150,
            "dropoff_lat": 3.8965,
            "dropoff_lng": 11.5450,
            "payment_mode": "MOMO",
            "ride_type": "SOLO",
            "proposed_price": 2500.0
        }
    )
    ride_id = ride_resp.json()["id"]
    share_token = ride_resp.json()["share_token"]

    # Déclenchement de l'alerte SOS par le passager
    sos_resp = await client.post(
        f"/api/v1/rides/{ride_id}/sos",
        headers=p_headers,
        json={"latitude": 3.8955, "longitude": 11.5200, "message": "Problème sur l'itinéraire Bastos"}
    )
    assert sos_resp.status_code == 200
    sos_data = sos_resp.json()
    assert sos_data["is_sos_active"] is True
    assert "SMS_DISPATCHED" in sos_data["alert_status"]

    # Consultation du suivi public web sans authentification (famille / proches)
    public_resp = await client.get(f"/api/v1/tracking/{share_token}")
    assert public_resp.status_code == 200
    track_data = public_resp.json()
    assert track_data["is_sos_active"] is True
    assert track_data["pickup_name"] == "Carrefour Bastos"
    assert track_data["dropoff_name"] == "Hôpital Général"

