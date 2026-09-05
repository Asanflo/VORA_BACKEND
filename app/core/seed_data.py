from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.poi import POI
from app.models.user import User, DriverProfile, UserRole, VerificationStatus
from app.models.weather import WeatherAlert, WeatherAlertType, AlertSeverity
from app.core.security import normalize_cameroon_phone
import json

POIS_DATA = [
    # --- YAOUNDE ---
    {
        "name": "Carrefour EMIA",
        "city": "Yaoundé",
        "category": "Carrefour",
        "latitude": 3.8568,
        "longitude": 11.5015,
        "aliases_json": json.dumps(["EMIA", "Carrefour Militaire", "Ecole Militaire", "Melien EMIA"]),
        "popularity_score": 95,
        "description": "Repère majeur près de l'École Militaire Interarmées et du quartier Melen."
    },
    {
        "name": "Marché Mokolo",
        "city": "Yaoundé",
        "category": "Marché",
        "latitude": 3.8741,
        "longitude": 11.5032,
        "aliases_json": json.dumps(["Mokolo", "Grand Marché Mokolo", "Mokolo En-bas", "Mokolo Madagascar"]),
        "popularity_score": 98,
        "description": "Le plus grand marché populaire de friperie et vivres de Yaoundé."
    },
    {
        "name": "Pharmacie du Soleil",
        "city": "Yaoundé",
        "category": "Pharmacie",
        "latitude": 3.8642,
        "longitude": 11.5186,
        "aliases_json": json.dumps(["Soleil", "Pharmacie Soleil", "Carrefour Soleil", "Centre-ville Soleil"]),
        "popularity_score": 90,
        "description": "Pharmacie historique située au cœur du centre commercial de Yaoundé."
    },
    {
        "name": "Total Melen",
        "city": "Yaoundé",
        "category": "Station-Service",
        "latitude": 3.8512,
        "longitude": 11.4981,
        "aliases_json": json.dumps(["Melen", "Station Melen", "Carrefour Melen", "Total Mini-ferme"]),
        "popularity_score": 88,
        "description": "Station Total face au CHU et au campus de Ngoa-Ekelle."
    },
    {
        "name": "Poste Centrale",
        "city": "Yaoundé",
        "category": "Administration",
        "latitude": 3.8667,
        "longitude": 11.5198,
        "aliases_json": json.dumps(["Poste", "Campost", "Poste Centrale Yaoundé", "Monument Poste"]),
        "popularity_score": 99,
        "description": "Point zéro historique et carrefour de transit pour tous les taxis jaunes."
    },
    {
        "name": "Carrefour Nlongkak",
        "city": "Yaoundé",
        "category": "Carrefour",
        "latitude": 3.8821,
        "longitude": 11.5234,
        "aliases_json": json.dumps(["Nlongkak", "Rond-point Nlongkak", "Vallée Nlongkak"]),
        "popularity_score": 92,
        "description": "Nœud de communication reliant Bastos, Djoungolo et Omnisports."
    },
    {
        "name": "Carrefour Warda",
        "city": "Yaoundé",
        "category": "Carrefour",
        "latitude": 3.8689,
        "longitude": 11.5122,
        "aliases_json": json.dumps(["Warda", "Palais des Sports", "Pont Warda", "Carrefour Bois Sainte Anastasie"]),
        "popularity_score": 91,
        "description": "Proche du Palais Polyvalent des Sports et du Bois Sainte Anastasie."
    },
    {
        "name": "Carrefour Bastos",
        "city": "Yaoundé",
        "category": "Carrefour",
        "latitude": 3.8950,
        "longitude": 11.5150,
        "aliases_json": json.dumps(["Bastos", "Rond-point Bastos", "Ambassades", "Carrefour Restaurant"]),
        "popularity_score": 87,
        "description": "Quartier diplomatique et résidentiel de standing."
    },
    {
        "name": "Carrefour Biyem-Assi (Rond-Point Express)",
        "city": "Yaoundé",
        "category": "Carrefour",
        "latitude": 3.8375,
        "longitude": 11.4880,
        "aliases_json": json.dumps(["Rond-point Express", "Biyem-Assi Express", "Carrefour Biyem-Assi", "Express"]),
        "popularity_score": 94,
        "description": "Centre névralgique de Biyem-Assi avec forte concentration de taxis."
    },
    {
        "name": "Carrefour Obili",
        "city": "Yaoundé",
        "category": "Carrefour",
        "latitude": 3.8480,
        "longitude": 11.4920,
        "aliases_json": json.dumps(["Obili", "Chapelle Obili", "Carrefour École de Police"]),
        "popularity_score": 86,
        "description": "Zone universitaire estudiantine très animée."
    },
    {
        "name": "Carrefour Vogt",
        "city": "Yaoundé",
        "category": "Carrefour",
        "latitude": 3.8410,
        "longitude": 11.5105,
        "aliases_json": json.dumps(["Vogt", "Collège Vogt", "Carrefour Collège Vogt"]),
        "popularity_score": 83,
        "description": "Proche du collège François-Xavier Vogt et de Mvolyé."
    },
    {
        "name": "Hôpital Général de Yaoundé",
        "city": "Yaoundé",
        "category": "Hôpital",
        "latitude": 3.8965,
        "longitude": 11.5450,
        "aliases_json": json.dumps(["Hôpital Général", "HGY", "Ngousso Hôpital"]),
        "popularity_score": 85,
        "description": "Grand centre hospitalier situé à Ngousso."
    },
    # --- DOUALA ---
    {
        "name": "Rond-Point Deido",
        "city": "Douala",
        "category": "Carrefour",
        "latitude": 4.0620,
        "longitude": 9.7115,
        "aliases_json": json.dumps(["Deido", "Rond-Point Deido", "Feu Rouge Deido", "Monument Deido"]),
        "popularity_score": 99,
        "description": "Le repère emblématique d'entrée du pont sur le Wouri à Douala."
    },
    {
        "name": "Carrefour Ndokoti",
        "city": "Douala",
        "category": "Carrefour",
        "latitude": 4.0450,
        "longitude": 9.7420,
        "aliases_json": json.dumps(["Ndokoti", "Carrefour Ange Ndokoti", "Tunnel Ndokoti"]),
        "popularity_score": 98,
        "description": "Nœud de circulation le plus dense reliant Bassa, Cité des Palmiers et Nyalla."
    },
    {
        "name": "Carrefour Ange Raphaël",
        "city": "Douala",
        "category": "Carrefour",
        "latitude": 4.0535,
        "longitude": 9.7280,
        "aliases_json": json.dumps(["Ange Raphaël", "Campus Ange Raphaël", "Université de Douala"]),
        "popularity_score": 94,
        "description": "Repère majeur face au campus de l'Université de Douala."
    },
    {
        "name": "Marché Sandaga",
        "city": "Douala",
        "category": "Marché",
        "latitude": 4.0485,
        "longitude": 9.7040,
        "aliases_json": json.dumps(["Sandaga", "Marché Vivres Sandaga"]),
        "popularity_score": 89,
        "description": "Grand marché de denrées alimentaires et carrefour de taxis."
    },
    {
        "name": "Akwa Palace",
        "city": "Douala",
        "category": "Hôtel",
        "latitude": 4.0510,
        "longitude": 9.6970,
        "aliases_json": json.dumps(["Akwa", "Boulevard de la Liberté", "Hôtel Akwa Palace"]),
        "popularity_score": 93,
        "description": "Cœur du quartier des affaires d'Akwa."
    },
    {
        "name": "Place du Gouvernement (Bonanjo)",
        "city": "Douala",
        "category": "Administration",
        "latitude": 4.0425,
        "longitude": 9.6880,
        "aliases_json": json.dumps(["Bonanjo", "Place du Gouvernement", "Services du Gouverneur"]),
        "popularity_score": 90,
        "description": "Centre administratif historique de Douala."
    }
]

WEATHER_ALERTS_DATA = [
    {
        "title": "Axe Submergé / Forte Pluie - Warda",
        "alert_type": WeatherAlertType.FLOODING,
        "severity": AlertSeverity.WARNING,
        "city": "Yaoundé",
        "latitude": 3.8689,
        "longitude": 11.5122,
        "radius_meters": 750.0,
        "fare_multiplier": 1.25,
        "eta_penalty_minutes": 15,
        "description": "Montée des eaux au niveau du carrefour Warda suite aux averses tropicales. Vitesse réduite.",
        "is_active": True
    },
    {
        "title": "Embouteillage Monstre & Chaussée Glissante - Ndokoti",
        "alert_type": WeatherAlertType.TRAFFIC_JAM,
        "severity": AlertSeverity.DANGER,
        "city": "Douala",
        "latitude": 4.0450,
        "longitude": 9.7420,
        "radius_meters": 1200.0,
        "fare_multiplier": 1.30,
        "eta_penalty_minutes": 25,
        "description": "Trafic saturé et chaussée dégradée à Ndokoti. Majoration incitative chauffeur activée.",
        "is_active": True
    }
]

async def seed_initial_data(session: AsyncSession) -> None:
    """Insère les données de démarrage si la base est vide (repères, alertes, comptes test)"""
    
    # 1. Vérifier si les POIs existent déjà
    result = await session.exec(select(POI))
    existing_poi = result.first()
    if not existing_poi:
        for poi_data in POIS_DATA:
            poi = POI(**poi_data)
            session.add(poi)
        await session.commit()
    
    # 2. Vérifier les alertes météo
    result = await session.exec(select(WeatherAlert))
    existing_alert = result.first()
    if not existing_alert:
        for alert_data in WEATHER_ALERTS_DATA:
            alert = WeatherAlert(**alert_data)
            session.add(alert)
        await session.commit()

    # 3. Comptes de démonstration : Passager & Chauffeur vérifié
    result = await session.exec(select(User).where(User.phone_number == "+237699112233"))
    passenger = result.first()
    if not passenger:
        passenger = User(
            phone_number="+237699112233",
            full_name="Jean-Marc Atangana",
            role=UserRole.PASSENGER
        )
        session.add(passenger)
        await session.commit()

    result = await session.exec(select(User).where(User.phone_number == "+237677445566"))
    driver_user = result.first()
    if not driver_user:
        driver_user = User(
            phone_number="+237677445566",
            full_name="Paul Mbida (Chauffeur Vérifié)",
            role=UserRole.DRIVER
        )
        session.add(driver_user)
        await session.commit()
        await session.refresh(driver_user)

        driver_profile = DriverProfile(
            user_id=driver_user.id,
            cni_number="118293041",
            cni_document_url="https://vora.cm/docs/demo_cni_mbida.jpg",
            driver_license_number="PC-2018-84729",
            driver_license_document_url="https://vora.cm/docs/demo_permis_mbida.jpg",
            vehicle_registration_doc_url="https://vora.cm/docs/demo_cg_mbida.jpg",
            taxi_door_number="YDE-1420",
            vehicle_plate="CE 789 AA",
            car_model_color="Toyota Carina E Jaune VORA",
            verification_status=VerificationStatus.VERIFIED,
            badges_json=json.dumps(["CNI_VERIFIEE", "PERMIS_VALIDE", "TAXI_COMMUNAL_HOMOLOGUE", "CHAUFFEUR_TOP_NOTE"]),
            rating_avg=4.9,
            rides_completed_count=342,
            wallet_balance=15000.0,
            current_latitude=3.8568,
            current_longitude=11.5015,
            is_available=True
        )
        session.add(driver_profile)
        await session.commit()
