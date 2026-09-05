from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.models.ride import Ride
from app.models.user import User
from app.schemas.sos import SOSTriggerRequest, SOSAlertRead
from app.services.sos_service import SOSService
from app.api.deps import get_current_user
from app.api.websocket.connection_manager import manager

router = APIRouter(prefix="/rides/{ride_id}/sos", tags=["Sécurité & Mode SOS"])

@router.post("", response_model=SOSAlertRead, summary="Déclencher une alerte SOS d'urgence")
async def trigger_emergency_sos(
    ride_id: int,
    req: SOSTriggerRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Bouton d'urgence SOS :
    - Marque la course en alerte d'urgence
    - Diffuse les coordonnées GPS aux services de secours
    - Génère un lien de suivi en direct à partager avec les proches
    """
    ride = await session.get(Ride, ride_id)
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course introuvable.")

    if current_user.id != ride.passenger_id and current_user.id != ride.driver_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Non autorisé sur cette course.")

    sos_alert = await SOSService.trigger_sos_alert(
        session=session,
        ride=ride,
        current_lat=req.latitude,
        current_lng=req.longitude,
        custom_message=req.message
    )

    # Diffusion immédiate de l'alerte maximale sur WebSocket
    await manager.broadcast_to_ride(ride_id, "sos:alert", {
        "ride_id": ride_id,
        "is_sos_active": True,
        "latitude": req.latitude,
        "longitude": req.longitude,
        "tracking_url": sos_alert.public_tracking_url,
        "alert_status": "HIGH_PRIORITY_EMERGENCY"
    })

    return sos_alert
