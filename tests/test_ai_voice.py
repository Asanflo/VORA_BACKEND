import pytest

@pytest.mark.asyncio
async def test_ai_voice_pidgin_and_camfranglais_parsing(client):
    # Test 1 : Phrase en Pidgin camerounais ("Drop me for Carrefour EMIA")
    resp_pidgin = await client.post(
        "/api/v1/ai/voice-intent",
        json={"text": "Drop me for Carrefour EMIA"}
    )
    assert resp_pidgin.status_code == 200
    data_p = resp_pidgin.json()
    assert data_p["dropoff_poi"] is not None
    assert data_p["dropoff_poi"]["name"] == "Carrefour EMIA"
    assert data_p["ride_type"] == "SOLO"
    assert data_p["suggested_price_fcfa"] > 0
    assert len(data_p["assistant_reply"]) > 0

    # Test 2 : Phrase avec covoiturage / partage ("Carry me go Marché Mokolo en covoiturage")
    resp_shared = await client.post(
        "/api/v1/ai/voice-intent",
        json={"text": "Carry me go Marché Mokolo en covoiturage"}
    )
    assert resp_shared.status_code == 200
    data_s = resp_shared.json()
    assert data_s["dropoff_poi"] is not None
    assert "Mokolo" in data_s["dropoff_poi"]["name"]
    assert data_s["ride_type"] == "SHARED"

    # Test 3 : Phrase en Camfranglais ("Tu me drop à la Pharmacie du Soleil")
    resp_camfranglais = await client.post(
        "/api/v1/ai/voice-intent",
        json={"text": "Tu me drop à la Pharmacie du Soleil stp"}
    )
    assert resp_camfranglais.status_code == 200
    data_c = resp_camfranglais.json()
    assert data_c["dropoff_poi"] is not None
    assert "Soleil" in data_c["dropoff_poi"]["name"]
