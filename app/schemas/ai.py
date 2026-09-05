from typing import Optional
from pydantic import BaseModel
from app.models.ride import RideType
from app.schemas.poi import POIRead

class VoiceIntentRequest(BaseModel):
    text: str  # Texte transcrit par Flutter ou dicté (support Camfranglais & Pidgin)

class VoiceIntentResponse(BaseModel):
    raw_input: str
    pickup_landmark: Optional[str] = None
    dropoff_landmark: Optional[str] = None
    ride_type: RideType = RideType.SOLO
    confidence: float
    pickup_poi: Optional[POIRead] = None
    dropoff_poi: Optional[POIRead] = None
    suggested_price_fcfa: float
    assistant_reply: str
