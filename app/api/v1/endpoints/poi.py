from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import json
from app.core.database import get_session
from app.models.poi import POI
from app.schemas.poi import POICreate, POIRead, POINearestResponse
from app.services.poi_service import POIService

router = APIRouter(prefix="/poi", tags=["Repères Locaux (Points d'Intérêt)"])

@router.get("/search", response_model=List[POIRead], summary="Recherche par repères populaires (ex: Carrefour EMIA, Mokolo)")
async def search_landmarks(
    q: str = Query(..., min_length=1, description="Nom, mot-clé ou alias du repère (ex: 'EMIA', 'Mokolo', 'Soleil')"),
    city: Optional[str] = Query(None, description="Filtrer par ville (Yaoundé, Douala)"),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session)
):
    """
    Recherche intelligente par repères locaux au Cameroun :
    Gère les fautes de frappe, la recherche par sous-chaînes, les catégories et les acronymes/alias populaires.
    """
    pois = await POIService.search_pois(session, query=q, city=city, limit=limit)
    return pois

@router.get("/nearest", response_model=POINearestResponse, summary="Trouver le repère le plus proche d'une coordonnée GPS")
async def get_nearest_landmark(
    lat: float = Query(..., description="Latitude GPS"),
    lng: float = Query(..., description="Longitude GPS"),
    city: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """
    Reverse geocoding camerounais :
    Transforme une position GPS brute en repère familier (ex: 'À 45m de Carrefour EMIA').
    """
    nearest = await POIService.find_nearest_poi(session, lat=lat, lng=lng, city=city)
    if not nearest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun repère répertorié à proximité de ces coordonnées."
        )
    return nearest

@router.get("", response_model=List[POIRead], summary="Lister tous les repères")
async def list_landmarks(
    city: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """Liste tous les repères de la base avec possibilité de filtrer par ville ou catégorie"""
    stmt = select(POI)
    if city:
        stmt = stmt.where(POI.city.ilike(f"%{city}%"))
    if category:
        stmt = stmt.where(POI.category.ilike(f"%{category}%"))
    
    result = await session.exec(stmt)
    pois = result.all()
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
        for p in pois
    ]

@router.post("", response_model=POIRead, status_code=status.HTTP_201_CREATED, summary="Ajouter un nouveau repère")
async def create_landmark(
    poi_in: POICreate,
    session: AsyncSession = Depends(get_session)
):
    """Permet d'enrichir dynamiquement la cartographie des repères locaux"""
    poi = POI(
        name=poi_in.name,
        city=poi_in.city,
        category=poi_in.category,
        latitude=poi_in.latitude,
        longitude=poi_in.longitude,
        aliases_json=json.dumps(poi_in.aliases),
        popularity_score=poi_in.popularity_score,
        description=poi_in.description
    )
    session.add(poi)
    await session.commit()
    await session.refresh(poi)

    return POIRead(
        id=poi.id,
        name=poi.name,
        city=poi.city,
        category=poi.category,
        latitude=poi.latitude,
        longitude=poi.longitude,
        aliases=poi.aliases,
        popularity_score=poi.popularity_score,
        description=poi.description
    )
