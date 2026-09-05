import pytest

@pytest.mark.asyncio
async def test_shared_rides_automatic_grouping(client):
    # Passager 1
    resp_p1 = await client.post("/api/v1/auth/passenger/register", json={
        "phone_number": "691000001",
        "full_name": "Passager Un"
    })
    headers_p1 = {"Authorization": f"Bearer {resp_p1.json()['access_token']}"}

    # Passager 2
    resp_p2 = await client.post("/api/v1/auth/passenger/register", json={
        "phone_number": "691000002",
        "full_name": "Passager Deux"
    })
    headers_p2 = {"Authorization": f"Bearer {resp_p2.json()['access_token']}"}

    # Passager 1 réserve une course partagée (Total Melen -> Poste Centrale)
    ride1_resp = await client.post(
        "/api/v1/rides",
        headers=headers_p1,
        json={
            "pickup_name": "Total Melen",
            "dropoff_name": "Poste Centrale",
            "pickup_lat": 3.8512,
            "pickup_lng": 11.4981,
            "dropoff_lat": 3.8667,
            "dropoff_lng": 11.5198,
            "payment_mode": "MOMO",
            "ride_type": "SHARED",
            "proposed_price": 800.0
        }
    )
    assert ride1_resp.status_code == 201
    ride1_id = ride1_resp.json()["id"]

    # Passager 2 réserve une course partagée sur le même corridor (Carrefour EMIA proche de Melen -> Marché Central/Poste)
    ride2_resp = await client.post(
        "/api/v1/rides",
        headers=headers_p2,
        json={
            "pickup_name": "Carrefour EMIA",
            "dropoff_name": "Pharmacie du Soleil",
            "pickup_lat": 3.8568,
            "pickup_lng": 11.5015,
            "dropoff_lat": 3.8642,
            "dropoff_lng": 11.5186,
            "payment_mode": "MOMO",
            "ride_type": "SHARED",
            "proposed_price": 800.0
        }
    )
    assert ride2_resp.status_code == 201
    ride2_data = ride2_resp.json()
    assert ride2_data["shared_group_id"] is not None

    # Vérifier que la course 1 a été mise à jour avec le même shared_group_id
    ride1_check = await client.get(f"/api/v1/rides/{ride1_id}", headers=headers_p1)
    assert ride1_check.status_code == 200
    assert ride1_check.json()["shared_group_id"] == ride2_data["shared_group_id"]
