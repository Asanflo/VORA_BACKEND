from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import json
from app.core.database import get_session
from app.models.user import User, DriverProfile, UserRole, VerificationStatus
from app.api.deps import get_current_user, get_current_driver
from app.api.websocket.connection_manager import manager

router = APIRouter(prefix="/drivers", tags=["Chauffeurs Vérifiés & Profils de Confiance"])

class DriverLocationUpdate(BaseModel):
    latitude: float
    longitude: float

class DriverTrustProfileResponse(BaseModel):
    driver_id: int
    user_id: int
    full_name: str
    phone_number: str
    taxi_door_number: str       # ex: "YDE-1420"
    vehicle_plate: str          # ex: "CE 789 AA"
    car_model_color: str        # ex: "Toyota Carina E Jaune VORA"
    verification_status: VerificationStatus
    is_verified: bool
    rating_avg: float
    rides_completed_count: int
    verification_badges: List[str]
    cni_document_url: Optional[str] = None
    driver_license_document_url: Optional[str] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None

@router.get("/{driver_id}/profile", response_model=DriverTrustProfileResponse, summary="Fiche de confiance complète du chauffeur (Badge & Portière)")
async def get_driver_trust_profile(
    driver_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Fiche de confiance consultable par le passager :
    Affiche les badges de vérification (CNI + Permis validés), le numéro officiel de portière
    du taxi jaune (ex: YDE-1420), l'immatriculation et les notes.
    """
    driver_user = await session.get(User, driver_id)
    if not driver_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chauffeur introuvable.")

    stmt = select(DriverProfile).where(DriverProfile.user_id == driver_id)
    result = await session.exec(stmt)
    profile = result.first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil de taxi non trouvé.")

    # Masquage partiel du numéro de téléphone pour la vie privée
    phone = driver_user.phone_number
    masked_phone = f"{phone[:7]}****{phone[-2:]}" if len(phone) >= 9 else phone

    return DriverTrustProfileResponse(
        driver_id=profile.id,
        user_id=driver_user.id,
        full_name=driver_user.full_name,
        phone_number=masked_phone,
        taxi_door_number=profile.taxi_door_number,
        vehicle_plate=profile.vehicle_plate,
        car_model_color=profile.car_model_color,
        verification_status=profile.verification_status,
        is_verified=(profile.verification_status == VerificationStatus.VERIFIED),
        rating_avg=profile.rating_avg,
        rides_completed_count=profile.rides_completed_count,
        verification_badges=profile.badges,
        cni_document_url=profile.cni_document_url,
        driver_license_document_url=profile.driver_license_document_url,
        current_latitude=profile.current_latitude,
        current_longitude=profile.current_longitude
    )

@router.post("/location", summary="Mise à jour de la position GPS du chauffeur")
async def update_driver_location(
    req: DriverLocationUpdate,
    driver_profile: DriverProfile = Depends(get_current_driver),
    session: AsyncSession = Depends(get_session)
):
    """Permet à l'application Flutter chauffeur d'émettre sa position GPS en temps réel"""
    driver_profile.current_latitude = req.latitude
    driver_profile.current_longitude = req.longitude
    session.add(driver_profile)
    await session.commit()

    # Diffusion globale pour le dispatch Flutter
    await manager.broadcast_global("driver:location_updated", {
        "driver_id": driver_profile.user_id,
        "taxi_door_number": driver_profile.taxi_door_number,
        "latitude": req.latitude,
        "longitude": req.longitude
    })

    return {"success": True, "latitude": req.latitude, "longitude": req.longitude}

@router.post("/{driver_id}/verify", summary="Validation administrative des pièces (Attribution du badge Vérifié)")
async def admin_verify_driver(
    driver_id: int,
    session: AsyncSession = Depends(get_session)
):
    """
    Valide les pièces d'un chauffeur (CNI, Permis, Portière taxi) et lui octroie le badge
    'CHAUFFEUR_VERIFIE' ainsi que 'TAXI_COMMUNAL_HOMOLOGUE'.
    """
    stmt = select(DriverProfile).where(DriverProfile.user_id == driver_id)
    result = await session.exec(stmt)
    profile = result.first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profil chauffeur introuvable.")

    profile.verification_status = VerificationStatus.VERIFIED
    profile.badges = [
        "CNI_VERIFIEE",
        "PERMIS_VALIDE",
        "TAXI_COMMUNAL_HOMOLOGUE",
        "CHAUFFEUR_VERIFIE_VORA"
    ]
    session.add(profile)
    await session.commit()
    await session.refresh(profile)

    return {
        "success": True,
        "driver_id": driver_id,
        "verification_status": profile.verification_status,
        "badges": profile.badges,
        "message": "Chauffeur vérifié avec succès. Les badges de confiance sont désormais actifs."
    }
