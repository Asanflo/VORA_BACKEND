import math
from typing import List, Optional, Tuple
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.poi import POI
from app.schemas.poi import POIRead, POINearestResponse

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcule la distance géodésique en mètres entre deux coordonnées GPS"""
    R = 6371000.0  # Rayon de la Terre en mètres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

class POIService:
    @staticmethod
    async def search_pois(
        session: AsyncSession,
        query: str,
        city: Optional[str] = None,
        limit: int = 10
    ) -> List[POIRead]:
        """
        Moteur de recherche par repères populaires (Carrefour EMIA, Marché Mokolo, etc.).
        Cherche par nom officiel, catégorie et mots-clés/alias populaires.
        """
        stmt = select(POI)
        if city:
            stmt = stmt.where(POI.city.ilike(f"%{city}%"))
        
        result = await session.exec(stmt)
        all_pois = result.all()

        query_clean = query.strip().lower()
        scored_pois: List[Tuple[float, POI]] = []

        for poi in all_pois:
            score = 0.0
            poi_name_lower = poi.name.lower()
            
            # Correspondance exacte ou préfixe
            if query_clean == poi_name_lower:
                score += 100.0
            elif query_clean in poi_name_lower:
                score += 60.0
            elif poi_name_lower in query_clean:
                score += 55.0
            
            # Correspondance dans les alias populaires (ex: "EMIA" -> "Carrefour EMIA")
            for alias in poi.aliases:
                alias_lower = alias.lower()
                if query_clean == alias_lower:
                    score += 80.0
                elif query_clean in alias_lower or alias_lower in query_clean:
                    score += 50.0
            
            # Catégorie (Carrefour, Marché, etc.)
            if query_clean in poi.category.lower():
                score += 30.0

            # Bonus de popularité du repère
            if score > 0:
                score += (poi.popularity_score * 0.1)
                scored_pois.append((score, poi))

        # Tri décroissant selon le score
        scored_pois.sort(key=lambda x: x[0], reverse=True)
        top_pois = [p for _, p in scored_pois[:limit]]

        return [
            POIRead(
                id=p.id,
                name=p.name,
                city=p.city,
                category=p.category,
                latitude=p.latitude,
                longitude=p.longitude,
                aliases=p.aliases,
                popularity_score=p.popularity_score,
                description=p.description
            )
            for p in top_pois
        ]

    @staticmethod
    async def find_nearest_poi(
        session: AsyncSession,
        lat: float,
        lng: float,
        city: Optional[str] = None
    ) -> Optional[POINearestResponse]:
        """
        Reverse geocoding local : trouve le repère populaire le plus proche
        d'une coordonnée GPS (ex: 'À 35m de Pharmacie du Soleil').
        """
        stmt = select(POI)
        if city:
            stmt = stmt.where(POI.city.ilike(f"%{city}%"))
        
        result = await session.exec(stmt)
        all_pois = result.all()
        if not all_pois:
            return None

        closest_poi = None
        min_dist = float("inf")

        for poi in all_pois:
            dist = haversine_distance_meters(lat, lng, poi.latitude, poi.longitude)
            if dist < min_dist:
                min_dist = dist
                closest_poi = poi

        if not closest_poi:
            return None

        # Formulation naturelle pour le Cameroun
        if min_dist < 50:
            label = f"Au niveau de {closest_poi.name}"
        elif min_dist < 1000:
            label = f"À {int(min_dist)}m de {closest_poi.name}"
        else:
            label = f"À {(min_dist/1000.0):.1f}km de {closest_poi.name}"

        poi_read = POIRead(
            id=closest_poi.id,
            name=closest_poi.name,
            city=closest_poi.city,
            category=closest_poi.category,
            latitude=closest_poi.latitude,
            longitude=closest_poi.longitude,
            aliases=closest_poi.aliases,
            popularity_score=closest_poi.popularity_score,
            description=closest_poi.description
        )

        return POINearestResponse(
            poi=poi_read,
            distance_meters=round(min_dist, 1),
            human_readable_label=label
        )
