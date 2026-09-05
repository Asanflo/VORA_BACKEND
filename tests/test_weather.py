import pytest

@pytest.mark.asyncio
async def test_weather_hazards_and_fare_multiplier(client):
    # Consultation des alertes météo actives
    resp_alerts = await client.get("/api/v1/weather-alerts/active?city=Yaoundé")
    assert resp_alerts.status_code == 200
    alerts = resp_alerts.json()
    assert len(alerts) > 0
    assert any("Warda" in a["title"] for a in alerts)

    # Estimation d'une course traversant la zone inondée de Warda
    # Warda est à (3.8689, 11.5122)
    resp_est = await client.post(
        "/api/v1/rides/estimate",
        json={
            "pickup_lat": 3.8689,
            "pickup_lng": 11.5122,
            "dropoff_lat": 3.8821,
            "dropoff_lng": 11.5234,
            "ride_type": "SOLO"
        }
    )
    assert resp_est.status_code == 200
    est = resp_est.json()
    # La majoration météo doit être appliquée (> 1.0)
    assert est["weather_multiplier"] >= 1.20
    assert est["weather_surcharge_amount"] > 0
