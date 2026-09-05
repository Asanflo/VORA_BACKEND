from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class SOSTriggerRequest(BaseModel):
    latitude: float
    longitude: float
    message: Optional[str] = "Urgence VORA - Passager en détresse"

class SOSAlertRead(BaseModel):
    ride_id: int
    is_sos_active: bool
    sos_activated_at: datetime
    share_token: str
    public_tracking_url: str
    latitude: float
    longitude: float
    emergency_contacts_alerted: List[str]
    alert_status: str

class LiveTrackingResponse(BaseModel):
    ride_id: int
    share_token: str
    status: str
    is_locked: bool
    is_sos_active: bool
    pickup_name: str
    dropoff_name: str
    passenger_name: str
    driver_name: Optional[str] = None
    taxi_door_number: Optional[str] = None
    vehicle_plate: Optional[str] = None
    car_model_color: Optional[str] = None
    driver_rating: Optional[float] = None
    driver_current_latitude: Optional[float] = None
    driver_current_longitude: Optional[float] = None
    created_at: datetime
    started_at: Optional[datetime] = None
