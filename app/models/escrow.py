from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
import enum

class EscrowStatus(str, enum.Enum):
    PENDING_HOLD = "PENDING_HOLD"
    HELD = "HELD"             # Fonds gelés sur le compte séquestre de l'agrégateur
    RELEASED = "RELEASED"     # Libéré vers le MoMo du chauffeur après validation du PIN
    REFUNDED = "REFUNDED"     # Remboursé au passager en cas d'annulation avant le démarrage

class PaymentProvider(str, enum.Enum):
    MTN_MOMO = "MTN_MOMO"
    ORANGE_MONEY = "ORANGE_MONEY"
    CASH = "CASH"

class EscrowTransaction(SQLModel, table=True):
    __tablename__ = "escrow_transactions"
    id: Optional[int] = Field(default=None, primary_key=True)
    ride_id: int = Field(foreign_key="rides.id", unique=True, index=True)
    passenger_phone: str
    driver_phone: Optional[str] = None
    amount: float = Field(description="Montant total de la course en FCFA")
    commission_amount: float = Field(default=0.0, description="Commission VORA prélevée")
    driver_net_amount: float = Field(default=0.0, description="Montant net reversé au chauffeur")
    provider: PaymentProvider = Field(default=PaymentProvider.MTN_MOMO)
    aggregator_reference: Optional[str] = Field(default=None, description="Référence de transaction de l'agrégateur")
    status: EscrowStatus = Field(default=EscrowStatus.PENDING_HOLD)
    held_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
