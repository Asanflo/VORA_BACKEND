from typing import Optional, List
import uuid
import math
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.ride import Ride, RideStatus, RideType
from app.services.poi_service import haversine_distance_meters

class SharedRideService:
    MAX_PICKUP_PROXIMITY_METERS = 2000.0   # Rayon max de 2 km entre les deux points de départ
    MAX_DROPOFF_PROXIMITY_METERS = 2500.0  # Rayon max de 2.5 km entre les deux destinations

    @classmethod
    async def find_and_match_shared_ride(
        cls,
        session: AsyncSession,
        new_ride: Ride
    ) -> Optional[str]:
        """
        Recherche une course partagée existante en attente ayant un corridor compatible.
        Si trouvée, associe les deux courses au même 'shared_group_id'.
        """
        if new_ride.ride_type != RideType.SHARED:
            return None

        # Rechercher des courses partagées en attente (sans groupe ou avec 1 seul passager)
        stmt = select(Ride).where(
            Ride.ride_type == RideType.SHARED,
            Ride.status.in_([RideStatus.REQUESTED, RideStatus.NEGOTIATING]),
            Ride.id != new_ride.id,
            Ride.shared_group_id == None
        )
        result = await session.exec(stmt)
        candidates = result.all()

        for candidate in candidates:
            # Calcul de la proximité des prises en charge
            pickup_dist = haversine_distance_meters(
                new_ride.pickup_lat, new_ride.pickup_lng,
                candidate.pickup_lat, candidate.pickup_lng
            )
            # Calcul de la proximité des destinations
            dropoff_dist = haversine_distance_meters(
                new_ride.dropoff_lat, new_ride.dropoff_lng,
                candidate.dropoff_lat, candidate.dropoff_lng
            )

            # Vérification de compatibilité de corridor
            if (pickup_dist <= cls.MAX_PICKUP_PROXIMITY_METERS and 
                dropoff_dist <= cls.MAX_DROPOFF_PROXIMITY_METERS):
                
                # Match trouvé ! Création d'un groupe partagé de taxi jaune
                group_id = f"SHARED-TAXI-{uuid.uuid4().hex[:8].upper()}"
                new_ride.shared_group_id = group_id
                candidate.shared_group_id = group_id
                
                session.add(new_ride)
                session.add(candidate)
                await session.commit()
                await session.refresh(new_ride)
                await session.refresh(candidate)
                
                return group_id

        return None
