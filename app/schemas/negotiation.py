from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.negotiation import OfferStatus

class NegotiationOfferCreate(BaseModel):
    offered_price: float
    driver_eta_minutes: int = 5

class NegotiationOfferRead(BaseModel):
    id: int
    ride_id: int
    driver_id: int
    driver_name: str
    driver_rating: float
    taxi_door_number: str
    car_model_color: str
    offered_price: float
    driver_eta_minutes: int
    status: OfferStatus
    created_at: datetime

