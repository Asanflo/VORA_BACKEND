from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from app.models.escrow import EscrowStatus, PaymentProvider

class EscrowRead(BaseModel):
    id: int
    ride_id: int
    amount: float
    commission_amount: float
    driver_net_amount: float
    provider: PaymentProvider
    aggregator_reference: Optional[str] = None
    status: EscrowStatus
    held_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
