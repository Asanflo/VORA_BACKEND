from typing import Optional, List
from pydantic import BaseModel
from app.models.user import UserRole, VerificationStatus

class UserLoginRequest(BaseModel):
    phone_number: str

class UserVerifyOTPRequest(BaseModel):
    phone_number: str
    otp_code: str = "1234"  # Mode démo/hackathon : 1234 ou tout code à 4 chiffres

class PassengerRegisterRequest(BaseModel):
    phone_number: str
    full_name: str

class DriverRegisterRequest(BaseModel):
    phone_number: str
    full_name: str
    cni_number: str
    cni_document_url: Optional[str] = None
    driver_license_number: str
    driver_license_document_url: Optional[str] = None
    vehicle_registration_doc_url: Optional[str] = None
    taxi_door_number: str  # ex: "YDE-1420"
    vehicle_plate: str     # ex: "CE 452 AA"
    car_model_color: str = "Toyota Corolla Jaune"

class UserRead(BaseModel):
    id: int
    phone_number: str
    full_name: str
    role: UserRole
    is_active: bool

class DriverProfileRead(BaseModel):
    id: int
    user_id: int
    cni_number: str
    driver_license_number: str
    taxi_door_number: str
    vehicle_plate: str
    car_model_color: str
    verification_status: VerificationStatus
    rating_avg: float
    rides_completed_count: int
    badges: List[str]
    wallet_balance: float
    cni_document_url: Optional[str] = None
    driver_license_document_url: Optional[str] = None
    vehicle_registration_doc_url: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
    driver_profile: Optional[DriverProfileRead] = None
