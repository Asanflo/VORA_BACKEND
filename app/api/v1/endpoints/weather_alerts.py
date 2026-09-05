from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.models.weather import WeatherAlert
from app.schemas.weather import WeatherAlertCreate, WeatherAlertRead
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather-alerts", tags=["Alertes Météo & État des Routes"])

@router.get("/active", response_model=List[WeatherAlertRead], summary="Alertes météo et nids-de-poule actives (Badges pour la carte Flutter)")
async def get_active_weather_hazards(
    city: str = Query("Yaoundé", description="Ville (Yaoundé, Douala)"),
    session: AsyncSession = Depends(get_session)
):
    """
    Fournit les zones à risque en temps réel pour affichage de badges visuels
    sur la carte interactive Flutter (Inondation, Pluie battante, Nids-de-poule, Embouteillages).
    """
    alerts = await WeatherService.get_active_alerts(session, city=city)
    return [
        WeatherAlertRead(
            id=a.id,
            title=a.title,
            alert_type=a.alert_type,
            severity=a.severity,
            city=a.city,
            latitude=a.latitude,
            longitude=a.longitude,
            radius_meters=a.radius_meters,
            fare_multiplier=a.fare_multiplier,
            eta_penalty_minutes=a.eta_penalty_minutes,
            is_active=a.is_active,
            description=a.description,
            created_at=a.created_at
        )
        for a in alerts
    ]

@router.post("", response_model=WeatherAlertRead, status_code=status.HTTP_201_CREATED, summary="Signaler une nouvelle zone à risque")
async def report_weather_hazard(
    alert_in: WeatherAlertCreate,
    session: AsyncSession = Depends(get_session)
):
    """Permet de créer une alerte météo ou un signalement de voie inondée"""
    alert = WeatherAlert(
        title=alert_in.title,
        alert_type=alert_in.alert_type,
        severity=alert_in.severity,
        city=alert_in.city,
        latitude=alert_in.latitude,
        longitude=alert_in.longitude,
        radius_meters=alert_in.radius_meters,
        fare_multiplier=alert_in.fare_multiplier,
        eta_penalty_minutes=alert_in.eta_penalty_minutes,
        description=alert_in.description,
        is_active=alert_in.is_active
    )
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return WeatherAlertRead(
        id=alert.id,
        title=alert.title,
        alert_type=alert.alert_type,
        severity=alert.severity,
        city=alert.city,
        latitude=alert.latitude,
        longitude=alert.longitude,
        radius_meters=alert.radius_meters,
        fare_multiplier=alert.fare_multiplier,
        eta_penalty_minutes=alert.eta_penalty_minutes,
        is_active=alert.is_active,
        description=alert.description,
        created_at=alert.created_at
    )
