from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import enum

class WeatherAlertType(str, enum.Enum):
    HEAVY_RAIN = "HEAVY_RAIN"           # Pluie battante
    FLOODING = "FLOODING"               # Inondation / axe submergé
    ROAD_DAMAGE = "ROAD_DAMAGE"         # Chaussée dégradée / nids-de-poule sévères / boue
    TRAFFIC_JAM = "TRAFFIC_JAM"         # Embouteillage critique

class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    DANGER = "DANGER"

class WeatherAlert(SQLModel, table=True):
    __tablename__ = "weather_alerts"
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(description="Intitulé de l'alerte (ex: Inondation Carrefour Mboppi)")
    alert_type: WeatherAlertType = Field(default=WeatherAlertType.HEAVY_RAIN)
    severity: AlertSeverity = Field(default=AlertSeverity.WARNING)
    city: str = Field(default="Yaoundé", index=True)
    latitude: float
    longitude: float
    radius_meters: float = Field(default=800.0, description="Rayon d'impact en mètres")
    fare_multiplier: float = Field(default=1.20, description="Majoration tarifaire incitative (ex: 1.20 = +20%)")
    eta_penalty_minutes: int = Field(default=10, description="Délai supplémentaire estimé en minutes")
    is_active: bool = Field(default=True, index=True)
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
