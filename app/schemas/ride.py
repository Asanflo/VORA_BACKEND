from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.ride import RideStatus, RideType, PaymentMode

class RideEstimateRequest(BaseModel):
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    ride_type: RideType = RideType.SOLO

class RideEstimateResponse(BaseModel):
    distance_km: float
    estimated_duration_minutes: int
    base_price: float
    weather_multiplier: float
    weather_surcharge_amount: float
    suggested_price_solo: float
    suggested_price_shared: float
    min_acceptable_offer: float
    max_acceptable_offer: float

class RideCreateRequest(BaseModel):
    pickup_name: str
    dropoff_name: str
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    pickup_poi_id: Optional[int] = None
    dropoff_poi_id: Optional[int] = None
    payment_mode: PaymentMode = PaymentMode.MOMO
    ride_type: RideType = RideType.SOLO
    proposed_price: Optional[float] = None  # Si omis, prend le suggested_price calculé

class RideRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    passenger_id: int
    driver_id: Optional[int] = None
    pickup_name: str
    dropoff_name: str
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    pickup_poi_id: Optional[int] = None
    dropoff_poi_id: Optional[int] = None
    payment_mode: PaymentMode
    ride_type: RideType
    suggested_price: float
    agreed_price: float
    status: RideStatus
    is_locked: bool
    secret_pin: Optional[str] = None  # Révélé uniquement au passager propriétaire de la course
    share_token: str
    is_sos_active: bool
    shared_group_id: Optional[str] = None
    commission_amount: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

class RideCompletePinRequest(BaseModel):
    pin: str  # Code PIN oral à 4 chiffres dicté par le passager

class RideActionResponse(BaseModel):
    success: bool
    status: RideStatus
    is_locked: bool
    message: str
    ride: Optional[RideRead] = None
