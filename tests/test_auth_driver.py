import pytest

@pytest.mark.asyncio
async def test_passenger_registration_and_login(client):
    # Inscription Passager
    resp = await client.post("/api/v1/auth/passenger/register", json={
        "phone_number": "690123456",
        "full_name": "Samuel Eto'o"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["phone_number"] == "+237690123456"
    assert data["user"]["role"] == "PASSENGER"

    # Connexion OTP
    otp_resp = await client.post("/api/v1/auth/verify-otp", json={
        "phone_number": "+237690123456",
        "otp_code": "1234"
    })
    assert otp_resp.status_code == 200
    assert otp_resp.json()["user"]["full_name"] == "Samuel Eto'o"

@pytest.mark.asyncio
async def test_driver_registration_with_mandatory_documents(client):
    # Inscription Chauffeur avec pièces d'identité et taxi jaune
    resp = await client.post("/api/v1/auth/driver/register", json={
        "phone_number": "671987654",
        "full_name": "Roger Milla (Chauffeur)",
        "cni_number": "100234958",
        "cni_document_url": "https://vora.cm/uploads/cni_milla.jpg",
        "driver_license_number": "PC-YDE-2021-994",
        "driver_license_document_url": "https://vora.cm/uploads/permis_milla.jpg",
        "vehicle_registration_doc_url": "https://vora.cm/uploads/cg_milla.jpg",
        "taxi_door_number": "YDE-8899",
        "vehicle_plate": "LT 991 BB",
        "car_model_color": "Toyota Yaris Jaune Taxi"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["role"] == "DRIVER"
    dp = data["driver_profile"]
    assert dp is not None
    assert dp["taxi_door_number"] == "YDE-8899"
    assert dp["verification_status"] == "PENDING_VERIFICATION"
    driver_user_id = data["user"]["id"]

    # Validation administrative du chauffeur
    verify_resp = await client.post(f"/api/v1/drivers/{driver_user_id}/verify")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verification_status"] == "VERIFIED"
    assert "CNI_VERIFIEE" in verify_resp.json()["badges"]

    # Consultation du profil de confiance public
    profile_resp = await client.get(f"/api/v1/drivers/{driver_user_id}/profile")
    assert profile_resp.status_code == 200
    prof = profile_resp.json()
    assert prof["is_verified"] is True
    assert prof["taxi_door_number"] == "YDE-8899"
    assert prof["vehicle_plate"] == "LT 991 BB"
