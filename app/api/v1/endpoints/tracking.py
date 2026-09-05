from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.models.ride import Ride
from app.models.user import User, DriverProfile
from app.schemas.sos import LiveTrackingResponse

router = APIRouter(prefix="/tracking", tags=["Suivi Public en Direct"])

@router.get("/{share_token}", response_model=LiveTrackingResponse, summary="Page web publique de suivi en temps réel (sans mot de passe)")
async def get_live_tracking_by_token(
    share_token: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Lien sécurisé pour les proches et la famille :
    Permet de suivre en direct l'avancement du taxi, l'identité du chauffeur,
    le numéro de portière communal et l'éventuelle alerte SOS, sans nécessiter de compte.
    """
    stmt = select(Ride).where(Ride.share_token == share_token)
    result = await session.exec(stmt)
    ride = result.first()

    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lien de suivi invalide ou expiré."
        )

    # Récupérer les informations passager
    passenger = await session.get(User, ride.passenger_id)
    passenger_name = passenger.full_name if passenger else "Passager VORA"

    # Récupérer les informations chauffeur
    driver_name = None
    taxi_door = None
    plate = None
    car_model = None
    rating = None
    lat = None
    lng = None

    if ride.driver_id:
        driver = await session.get(User, ride.driver_id)
        if driver:
            driver_name = driver.full_name
        stmt_dp = select(DriverProfile).where(DriverProfile.user_id == ride.driver_id)
        dp_res = await session.exec(stmt_dp)
        dp = dp_res.first()
        if dp:
            taxi_door = dp.taxi_door_number
            plate = dp.vehicle_plate
            car_model = dp.car_model_color
            rating = dp.rating_avg
            lat = dp.current_latitude
            lng = dp.current_longitude

    return LiveTrackingResponse(
        ride_id=ride.id,
        share_token=ride.share_token,
        status=ride.status,
        is_locked=ride.is_locked,
        is_sos_active=ride.is_sos_active,
        pickup_name=ride.pickup_name,
        dropoff_name=ride.dropoff_name,
        passenger_name=passenger_name,
        driver_name=driver_name,
        taxi_door_number=taxi_door,
        vehicle_plate=plate,
        car_model_color=car_model,
        driver_rating=rating,
        driver_current_latitude=lat,
        driver_current_longitude=lng,
        created_at=ride.created_at,
        started_at=ride.started_at
    )
