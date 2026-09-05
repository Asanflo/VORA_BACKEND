from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import enum

class OfferStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class NegotiationOffer(SQLModel, table=True):
    __tablename__ = "negotiation_offers"
    id: Optional[int] = Field(default=None, primary_key=True)
    ride_id: int = Field(foreign_key="rides.id", index=True)
    driver_id: int = Field(foreign_key="users.id", index=True)
    offered_price: float = Field(description="Montant proposé par le chauffeur en FCFA")
    driver_eta_minutes: int = Field(default=5, description="Temps estimé d'arrivée du chauffeur")
    status: OfferStatus = Field(default=OfferStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
