from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.weather import WeatherAlertType, AlertSeverity

class WeatherAlertCreate(BaseModel):
    title: str
    alert_type: WeatherAlertType = WeatherAlertType.HEAVY_RAIN
    severity: AlertSeverity = AlertSeverity.WARNING
    city: str = "Yaoundé"
    latitude: float
    longitude: float
    radius_meters: float = 800.0
    fare_multiplier: float = 1.20
    eta_penalty_minutes: int = 10
    description: Optional[str] = None
    is_active: bool = True

class WeatherAlertRead(BaseModel):
    id: int
    title: str
    alert_type: WeatherAlertType
    severity: AlertSeverity
    city: str
    latitude: float
    longitude: float
    radius_meters: float
    fare_multiplier: float
    eta_penalty_minutes: int
    is_active: bool
    description: Optional[str] = None
    created_at: datetime

