from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.models.user import User, DriverProfile
from app.models.ride import Ride
from app.schemas.negotiation import NegotiationOfferCreate, NegotiationOfferRead
from app.schemas.ride import RideRead
from app.services.negotiation_service import NegotiationService
from app.api.deps import get_current_user, get_current_driver
from app.api.websocket.connection_manager import manager

router = APIRouter(prefix="/rides/{ride_id}/negotiation", tags=["Système de Négociation & Tarif Flexible"])

@router.post("/offer", response_model=NegotiationOfferRead, summary="Chauffeur soumet une contre-proposition")
async def driver_counter_offer(
    ride_id: int,
    req: NegotiationOfferCreate,
    current_user: User = Depends(get_current_user),
    driver_profile: DriverProfile = Depends(get_current_driver),
    session: AsyncSession = Depends(get_session)
):
    """
    Permet au chauffeur de proposer un tarif personnalisé (ex: 1800 FCFA au lieu de 1500 FCFA).
    Notifie immédiatement le passager en temps réel via WebSockets.
    """
    success, msg, offer = await NegotiationService.make_driver_offer(
        session=session,
        ride_id=ride_id,
        driver_id=current_user.id,
        offered_price=req.offered_price,
        driver_eta_minutes=req.driver_eta_minutes
    )
    if not success or not offer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # Broadcast WebSocket vers le passager
    await manager.broadcast_to_ride(ride_id, "negotiation:offer_received", {
        "offer_id": offer.id,
        "driver_id": current_user.id,
        "driver_name": current_user.full_name,
        "rating": driver_profile.rating_avg,
        "taxi_door_number": driver_profile.taxi_door_number,
        "offered_price": offer.offered_price,
        "eta_minutes": offer.driver_eta_minutes
    })

    return NegotiationOfferRead(
        id=offer.id,
        ride_id=offer.ride_id,
        driver_id=offer.driver_id,
        driver_name=current_user.full_name,
        driver_rating=driver_profile.rating_avg,
        taxi_door_number=driver_profile.taxi_door_number,
        car_model_color=driver_profile.car_model_color,
        offered_price=offer.offered_price,
        driver_eta_minutes=offer.driver_eta_minutes,
        status=offer.status,
        created_at=offer.created_at
    )

@router.get("/offers", response_model=List[NegotiationOfferRead], summary="Lister les offres reçues pour une course")
async def list_offers(
    ride_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Permet au passager de consulter les propositions des différents chauffeurs de taxi jaune"""
    return await NegotiationService.get_ride_offers(session, ride_id)

@router.post("/offers/{offer_id}/accept", response_model=RideRead, summary="Passager valide l'offre d'un chauffeur")
async def accept_offer(
    ride_id: int,
    offer_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Le passager choisit l'offre qui lui convient le mieux (prix / ETA / note du chauffeur).
    Le tarif convenu est alors figé.
    """
    success, msg, ride = await NegotiationService.accept_offer(
        session=session,
        ride_id=ride_id,
        offer_id=offer_id,
        passenger_id=current_user.id
    )
    if not success or not ride:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    # Notifier tous les chauffeurs de la décision
    await manager.broadcast_to_ride(ride_id, "negotiation:offer_accepted", {
        "ride_id": ride.id,
        "accepted_offer_id": offer_id,
        "agreed_price": ride.agreed_price,
        "driver_id": ride.driver_id
    })

    return RideRead.model_validate(ride)
