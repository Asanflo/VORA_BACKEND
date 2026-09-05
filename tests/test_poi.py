import pytest

@pytest.mark.asyncio
async def test_search_pois_by_name_and_alias(client):
    # Recherche par acronyme / alias : "EMIA" -> "Carrefour EMIA"
    resp = await client.get("/api/v1/poi/search?q=EMIA")
    assert resp.status_code == 200
    pois = resp.json()
    assert len(pois) > 0
    assert "Carrefour EMIA" in [p["name"] for p in pois]

    # Recherche par nom : "Mokolo" -> "Marché Mokolo"
    resp_mokolo = await client.get("/api/v1/poi/search?q=Mokolo")
    assert resp_mokolo.status_code == 200
    pois_mokolo = resp_mokolo.json()
    assert any("Mokolo" in p["name"] for p in pois_mokolo)

    # Recherche par catégorie : "Pharmacie"
    resp_pharma = await client.get("/api/v1/poi/search?q=Pharmacie")
    assert resp_pharma.status_code == 200
    assert any("Pharmacie du Soleil" in p["name"] for p in resp_pharma.json())

@pytest.mark.asyncio
async def test_nearest_poi_reverse_geocoding(client):
    # Coordonnées très proches du Carrefour EMIA (3.8568, 11.5015)
    resp = await client.get("/api/v1/poi/nearest?lat=3.8569&lng=11.5016")
    assert resp.status_code == 200
    data = resp.json()
    assert data["poi"]["name"] == "Carrefour EMIA"
    assert data["distance_meters"] < 50.0
    assert "Carrefour EMIA" in data["human_readable_label"]
