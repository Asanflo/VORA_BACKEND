import math
from typing import Dict, Any
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.ride import RideType
from app.services.poi_service import haversine_distance_meters
from app.services.weather_service import WeatherService
from app.schemas.ride import RideEstimateResponse

class PricingService:
    BASE_SOLO_PRICE_FCFA = 1000.0       # Dépôt de base en taxi jaune
    PRICE_PER_KM_FCFA = 250.0           # Tarif kilométrique urbain
    SHARED_DISCOUNT_PERCENTAGE = 0.35   # -35% d'économie en course partagée
    URBAN_WINDING_FACTOR = 1.35         # Facteur d'itinéraire réel vs vol d'oiseau à Yaoundé/Douala

    @classmethod
    async def estimate_ride(
        cls,
        session: AsyncSession,
        pickup_lat: float,
        pickup_lng: float,
        dropoff_lat: float,
        dropoff_lng: float,
        ride_type: RideType = RideType.SOLO
    ) -> RideEstimateResponse:
        """Calcule l'estimation du prix conseillé, de la distance et de l'impact météo"""
        
        # 1. Distance estimée
        straight_dist_m = haversine_distance_meters(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
        road_dist_km = max(0.5, (straight_dist_m * cls.URBAN_WINDING_FACTOR) / 1000.0)

        # 2. Vitesse moyenne urbaine (~20 km/h dans les carrefours camerounais)
        avg_speed_kmh = 20.0
        base_duration_min = max(5, int((road_dist_km / avg_speed_kmh) * 60))

        # 3. Facteur météo et état des routes
        weather_multiplier, eta_penalty, impacted_alerts = await WeatherService.check_route_hazards(
            session, pickup_lat, pickup_lng, dropoff_lat, dropoff_lng
        )
        total_duration_min = base_duration_min + eta_penalty

        # 4. Calcul du prix brut solo
        raw_price_solo = cls.BASE_SOLO_PRICE_FCFA + (road_dist_km * cls.PRICE_PER_KM_FCFA)
        
        # Application de la majoration météo
        price_with_weather_solo = raw_price_solo * weather_multiplier
        
        # Arrondi aux 50 FCFA les plus proches
        suggested_solo = cls.round_fcfa(price_with_weather_solo)
        suggested_shared = cls.round_fcfa(suggested_solo * (1.0 - cls.SHARED_DISCOUNT_PERCENTAGE))

        # Calcul du supplément météo en valeur absolue
        weather_surcharge = cls.round_fcfa(raw_price_solo * (weather_multiplier - 1.0))

        # Fourchette de négociation recommandée (-25% à +40%)
        target_price = suggested_shared if ride_type == RideType.SHARED else suggested_solo
        min_offer = cls.round_fcfa(target_price * 0.75)
        max_offer = cls.round_fcfa(target_price * 1.40)

        return RideEstimateResponse(
            distance_km=round(road_dist_km, 2),
            estimated_duration_minutes=total_duration_min,
            base_price=cls.round_fcfa(raw_price_solo),
            weather_multiplier=round(weather_multiplier, 2),
            weather_surcharge_amount=weather_surcharge,
            suggested_price_solo=suggested_solo,
            suggested_price_shared=suggested_shared,
            min_acceptable_offer=min_offer,
            max_acceptable_offer=max_offer
        )

    @staticmethod
    def round_fcfa(amount: float) -> float:
        """Arrondit aux 50 FCFA les plus proches (pratique courante au Cameroun)"""
        return float(int(math.ceil(amount / 50.0) * 50))
