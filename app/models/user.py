from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
import enum
import json

class UserRole(str, enum.Enum):
    PASSENGER = "PASSENGER"
    DRIVER = "DRIVER"
    ADMIN = "ADMIN"

class VerificationStatus(str, enum.Enum):
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class UserBase(SQLModel):
    phone_number: str = Field(index=True, unique=True, description="Numéro au format camerounais (+237 6XXXXXXXX)")
    full_name: str
    role: UserRole = Field(default=UserRole.PASSENGER)
    is_active: bool = Field(default=True)

class User(UserBase, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    driver_profile: Optional["DriverProfile"] = Relationship(back_populates="user", sa_relationship_kwargs={"uselist": False})

class DriverProfileBase(SQLModel):
    cni_number: str = Field(description="Numéro de Carte Nationale d'Identité")
    cni_document_url: Optional[str] = Field(default=None, description="URL ou chemin du document CNI")
    driver_license_number: str = Field(description="Numéro du Permis de Conduire")
    driver_license_document_url: Optional[str] = Field(default=None, description="URL ou chemin du Permis")
    vehicle_registration_doc_url: Optional[str] = Field(default=None, description="Carte grise / Attestation du véhicule")
    taxi_door_number: str = Field(index=True, description="Numéro de portière communal du Taxi Jaune (ex: YDE-1420)")
    vehicle_plate: str = Field(index=True, description="Plaque d'immatriculation (ex: CE 345 BB)")
    car_model_color: str = Field(default="Toyota Corolla Jaune", description="Marque, modèle et couleur")
    verification_status: VerificationStatus = Field(default=VerificationStatus.PENDING_VERIFICATION)
    rating_avg: float = Field(default=5.0)
    rides_completed_count: int = Field(default=0)
    wallet_balance: float = Field(default=0.0, description="Solde du portefeuille chauffeur (déduction commission)")
    current_latitude: Optional[float] = Field(default=None)
    current_longitude: Optional[float] = Field(default=None)
    is_available: bool = Field(default=True)

class DriverProfile(DriverProfileBase, table=True):
    __tablename__ = "driver_profiles"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", unique=True, index=True)
    badges_json: str = Field(default='["NOUVEAU_CHAUFFEUR"]', description="JSON array des badges de confiance")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: Optional[User] = Relationship(back_populates="driver_profile")

    @property
    def badges(self) -> List[str]:
        try:
            return json.loads(self.badges_json)
        except Exception:
            return []

    @badges.setter
    def badges(self, value: List[str]):
        self.badges_json = json.dumps(value)
