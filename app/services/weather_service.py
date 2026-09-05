from typing import List, Tuple
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.weather import WeatherAlert
from app.services.poi_service import haversine_distance_meters

class WeatherService:
    @staticmethod
    async def get_active_alerts(session: AsyncSession, city: str = "Yaoundé") -> List[WeatherAlert]:
        """Récupère toutes les alertes météo et états de route actifs pour une ville"""
        stmt = select(WeatherAlert).where(
            WeatherAlert.is_active == True,
            WeatherAlert.city.ilike(f"%{city}%")
        )
        result = await session.exec(stmt)
        return list(result.all())

    @staticmethod
    async def check_route_hazards(
        session: AsyncSession,
        pickup_lat: float,
        pickup_lng: float,
        dropoff_lat: float,
        dropoff_lng: float
    ) -> Tuple[float, int, List[WeatherAlert]]:
        """
        Vérifie si le point de départ, de destination ou le trajet traverse des zones à alertes.
        Retourne : (fare_multiplier, eta_penalty_minutes, alerts_touching_route)
        """
        stmt = select(WeatherAlert).where(WeatherAlert.is_active == True)
        result = await session.exec(stmt)
        alerts = result.all()

        max_multiplier = 1.0
        total_eta_penalty = 0
        impacted_alerts: List[WeatherAlert] = []

        # Point médian du trajet pour approximer le couloir
        mid_lat = (pickup_lat + dropoff_lat) / 2.0
        mid_lng = (pickup_lng + dropoff_lng) / 2.0

        for alert in alerts:
            dist_pickup = haversine_distance_meters(pickup_lat, pickup_lng, alert.latitude, alert.longitude)
            dist_dropoff = haversine_distance_meters(dropoff_lat, dropoff_lng, alert.latitude, alert.longitude)
            dist_mid = haversine_distance_meters(mid_lat, mid_lng, alert.latitude, alert.longitude)

            # Si l'un des points est dans le rayon de l'alerte
            if (dist_pickup <= alert.radius_meters or 
                dist_dropoff <= alert.radius_meters or 
                dist_mid <= alert.radius_meters):
                
                impacted_alerts.append(alert)
                if alert.fare_multiplier > max_multiplier:
                    max_multiplier = alert.fare_multiplier
                total_eta_penalty += alert.eta_penalty_minutes

        return max_multiplier, total_eta_penalty, impacted_alerts
