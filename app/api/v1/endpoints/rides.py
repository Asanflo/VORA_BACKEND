from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.core.security import generate_oral_pin, generate_share_token, utc_now
from app.models.user import User, UserRole, DriverProfile
from app.models.ride import Ride, RideStatus, RideType, PaymentMode
from app.models.escrow import EscrowTransaction, EscrowStatus
from app.schemas.ride import (
    RideCreateRequest, RideRead, RideEstimateRequest,
    RideEstimateResponse, RideCompletePinRequest, RideActionResponse
)
from app.services.pricing_service import PricingService
from app.services.aggregator_service import PaymentAggregatorService
from app.services.shared_ride_service import SharedRideService
from app.api.deps import get_current_user, get_current_driver
from app.api.websocket.connection_manager import manager

router = APIRouter(prefix="/rides", tags=["Gestion des Courses & Séquestre"])

@router.post("/estimate", response_model=RideEstimateResponse, summary="Estimation tarifaire, distance et impact météo")
async def estimate_ride_fare(
    req: RideEstimateRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Calcule le tarif conseillé selon la distance réelle, la vitesse urbaine camerounaise,
    le type de course (Solo vs Partagée) et les majorations d'alertes météo/inondation.
    """
    return await PricingService.estimate_ride(
        session=session,
        pickup_lat=req.pickup_lat,
        pickup_lng=req.pickup_lng,
        dropoff_lat=req.dropoff_lat,
        dropoff_lng=req.dropoff_lng,
        ride_type=req.ride_type
    )

@router.post("", response_model=RideRead, status_code=status.HTTP_201_CREATED, summary="Réserver une course (Séquestre MoMo ou Espèces)")
async def create_ride(
    req: RideCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Création d'une course :
    - Mode MoMo : Pré-autorisation et gel immédiat des fonds sur le compte séquestre de l'agrégateur.
    - Mode Espèces : Réservation directe sans pré-autorisation bancaire.
    - Génération du Code PIN Oral à 4 chiffres (visible uniquement par le passager).
    - Mode Partagé : Recherche automatique d'un covoitureur compatible dans le même corridor.
    """
    # 1. Estimation tarifaire
    estimate = await PricingService.estimate_ride(
        session, req.pickup_lat, req.pickup_lng, req.dropoff_lat, req.dropoff_lng, req.ride_type
    )
    suggested = estimate.suggested_price_shared if req.ride_type == RideType.SHARED else estimate.suggested_price_solo
    agreed = req.proposed_price if req.proposed_price else suggested

    # 2. Génération des jetons de sécurité
    pin = generate_oral_pin()
    share_token = generate_share_token()

    ride = Ride(
        passenger_id=current_user.id,
        pickup_name=req.pickup_name,
        dropoff_name=req.dropoff_name,
        pickup_lat=req.pickup_lat,
        pickup_lng=req.pickup_lng,
        dropoff_lat=req.dropoff_lat,
        dropoff_lng=req.dropoff_lng,
        pickup_poi_id=req.pickup_poi_id,
        dropoff_poi_id=req.dropoff_poi_id,
        payment_mode=req.payment_mode,
        ride_type=req.ride_type,
        suggested_price=suggested,
        agreed_price=agreed,
        status=RideStatus.REQUESTED,
        is_locked=False,
        secret_pin=pin,
        share_token=share_token,
        created_at=utc_now()
    )
    session.add(ride)
    await session.commit()
    await session.refresh(ride)

    # 3. Séquestre Mobile Money si applicable (Étape 1 : Pré-autorisation & Blocage)
    if req.payment_mode == PaymentMode.MOMO:
        await PaymentAggregatorService.create_escrow_hold(
            session=session,
            ride=ride,
            passenger_phone=current_user.phone_number,
            amount=agreed
        )

    # 4. Covoiturage : Recherche et liaison de passagers compatibles
    if req.ride_type == RideType.SHARED:
        await SharedRideService.find_and_match_shared_ride(session, ride)

    # 5. Diffusion temps réel aux chauffeurs à proximité
    await manager.broadcast_global("ride:requested", {
        "ride_id": ride.id,
        "pickup_name": ride.pickup_name,
        "dropoff_name": ride.dropoff_name,
        "price": ride.agreed_price,
        "payment_mode": ride.payment_mode,
        "ride_type": ride.ride_type
    })

    return ride

@router.get("/{ride_id}", response_model=RideRead, summary="Détails d'une course")
async def get_ride(
    ride_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Retourne les détails d'une course.
    Règle de sécurité : Le Code PIN Oral n'est révélé qu'au passager qui a commandé la course.
    """
    ride = await session.get(Ride, ride_id)
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course introuvable.")

    ride_read = RideRead.model_validate(ride)
    # Masquer le PIN pour toute personne autre que le passager propriétaire
    if current_user.id != ride.passenger_id:
        ride_read.secret_pin = None

    return ride_read

@router.post("/{ride_id}/accept", response_model=RideActionResponse, summary="Chauffeur accepte la course")
async def accept_ride(
    ride_id: int,
    current_user: User = Depends(get_current_user),
    driver_profile: DriverProfile = Depends(get_current_driver),
    session: AsyncSession = Depends(get_session)
):
    """Étape 2 : Un chauffeur de taxi jaune accepte la course."""
    ride = await session.get(Ride, ride_id)
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course introuvable.")

    if ride.status not in [RideStatus.REQUESTED, RideStatus.NEGOTIATING]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Course non disponible (statut: {ride.status}).")

    ride.driver_id = current_user.id
    ride.status = RideStatus.ACCEPTED
    session.add(ride)
    await session.commit()
    await session.refresh(ride)

    # Notifier le passager
    await manager.broadcast_to_ride(ride_id, "ride:accepted", {
        "ride_id": ride.id,
        "status": ride.status,
        "driver_name": current_user.full_name,
        "taxi_door_number": driver_profile.taxi_door_number,
        "vehicle_plate": driver_profile.vehicle_plate,
        "rating": driver_profile.rating_avg
    })

    return RideActionResponse(
        success=True,
        status=ride.status,
        is_locked=ride.is_locked,
        message=f"Course #{ride_id} acceptée. Rendez-vous au repère : {ride.pickup_name}.",
        ride=RideRead.model_validate(ride)
    )

@router.post("/{ride_id}/start", response_model=RideActionResponse, summary="Chauffeur démarre la course (Verrouillage absolu)")
async def start_ride(
    ride_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Étape 3 : Chauffeur clique 'Démarrer la course'.
    RÈGLE D'ARRÊT CRITIQUE :
    - La course passe en 'STARTED' et 'is_locked = True'.
    - L'option 'Annuler' disparaît définitivement de l'écran du passager.
    """
    ride = await session.get(Ride, ride_id)
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course introuvable.")

    if ride.driver_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'êtes pas le chauffeur assigné à cette course.")

    if ride.status != RideStatus.ACCEPTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Impossible de démarrer la course avec le statut : {ride.status}.")

    ride.status = RideStatus.STARTED
    ride.is_locked = True
    ride.started_at = utc_now()
    session.add(ride)
    await session.commit()
    await session.refresh(ride)

    # Notifier le passager du verrouillage
    await manager.broadcast_to_ride(ride_id, "ride:started", {
        "ride_id": ride.id,
        "status": ride.status,
        "is_locked": True,
        "message": "Le chauffeur a démarré la course. Le trajet est verrouillé."
    })

    return RideActionResponse(
        success=True,
        status=ride.status,
        is_locked=True,
        message="Course démarrée avec succès. Le trajet est verrouillé.",
        ride=RideRead.model_validate(ride)
    )

@router.post("/{ride_id}/complete-with-pin", response_model=RideActionResponse, summary="Validation de fin de course MoMo par Code PIN Oral")
async def complete_ride_with_pin(
    ride_id: int,
    req: RideCompletePinRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Étape 5 (Scénario MoMo) :
    À destination, le passager dicte son code PIN oral à 4 chiffres (sans sortir son téléphone).
    Le chauffeur saisit le PIN.
    Si valide, les fonds sont instantanément libérés du compte séquestre de l'agrégateur vers le MoMo du chauffeur.
    """
    ride = await session.get(Ride, ride_id)
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course introuvable.")

    if ride.driver_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul le chauffeur de la course peut saisir le code PIN.")

    success, message, transaction = await PaymentAggregatorService.release_escrow_with_pin(
        session=session,
        ride=ride,
        entered_pin=req.pin,
        driver_phone=current_user.phone_number
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Diffusion en temps réel de la libération des fonds
    await manager.broadcast_to_ride(ride_id, "ride:completed", {
        "ride_id": ride.id,
        "status": ride.status,
        "payment_mode": "MOMO",
        "escrow_status": "RELEASED",
        "amount_released": transaction.driver_net_amount if transaction else ride.agreed_price
    })

    return RideActionResponse(
        success=True,
        status=ride.status,
        is_locked=ride.is_locked,
        message=message,
        ride=RideRead.model_validate(ride)
    )

@router.post("/{ride_id}/complete-cash", response_model=RideActionResponse, summary="Validation de fin de course en Espèces (Cash)")
async def complete_ride_cash(
    ride_id: int,
    current_user: User = Depends(get_current_user),
    driver_profile: DriverProfile = Depends(get_current_driver),
    session: AsyncSession = Depends(get_session)
):
    """
    Étape 4 (Scénario Espèces) :
    À l'arrivée, le passager remet les espèces en main propre.
    Le chauffeur clique simplement sur 'Valider / Terminer la course' (pas besoin de code PIN).
    La course est clôturée et la commission VORA est déduite sur le portefeuille du chauffeur.
    """
    ride = await session.get(Ride, ride_id)
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course introuvable.")

    if ride.driver_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul le chauffeur de la course peut clôturer le trajet.")

    if ride.payment_mode != PaymentMode.CASH:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cette course n'est pas en mode Espèces. Utilisez la validation par PIN.")

    success, message = await PaymentAggregatorService.process_cash_completion(
        session=session,
        ride=ride,
        driver_profile=driver_profile
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    # Diffusion en temps réel
    await manager.broadcast_to_ride(ride_id, "ride:completed", {
        "ride_id": ride.id,
        "status": ride.status,
        "payment_mode": "CASH",
        "message": "Paiement en espèces effectué. Trajet terminé."
    })

    return RideActionResponse(
        success=True,
        status=ride.status,
        is_locked=ride.is_locked,
        message=message,
        ride=RideRead.model_validate(ride)
    )

@router.post("/{ride_id}/cancel", response_model=RideActionResponse, summary="Annuler la course (Interdit après démarrage)")
async def cancel_ride(
    ride_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Annulation de course :
    RÈGLE D'ARRÊT : Si la course a déjà démarré (is_locked == True), l'annulation est strictement rejetée.
    Si elle n'a pas démarré, les fonds séquestrés MoMo sont intégralement remboursés au passager.
    """
    ride = await session.get(Ride, ride_id)
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course introuvable.")

    if current_user.id not in [ride.passenger_id, ride.driver_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non autorisé à annuler cette course.")

    # Règle d'arrêt stricte
    if ride.is_locked or ride.status == RideStatus.STARTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'annuler : la course est verrouillée car le chauffeur a déjà démarré le trajet."
        )

    if ride.status in [RideStatus.COMPLETED, RideStatus.CANCELLED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Course déjà terminée ou annulée ({ride.status}).")

    success, message, transaction = await PaymentAggregatorService.refund_escrow(session, ride)

    # Diffusion de l'annulation
    await manager.broadcast_to_ride(ride_id, "ride:cancelled", {
        "ride_id": ride.id,
        "cancelled_by": current_user.full_name,
        "message": message
    })

    return RideActionResponse(
        success=True,
        status=ride.status,
        is_locked=ride.is_locked,
        message=message,
        ride=RideRead.model_validate(ride)
    )
