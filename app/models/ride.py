from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
import enum
import secrets
from app.core.security import utc_now

class PaymentMode(str, enum.Enum):
    MOMO = "MOMO"
    CASH = "CASH"

class RideType(str, enum.Enum):
    SOLO = "SOLO"       # Course privée exclusive (dépôt)
    SHARED = "SHARED"   # Covoiturage / Dépôt partagé en taxi jaune

class RideStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"       # Réservée par le passager (si MoMo, séquestre gelé)
    NEGOTIATING = "NEGOTIATING"   # En négociation de tarif
    ACCEPTED = "ACCEPTED"         # Chauffeur a accepté, en route vers le passager
    STARTED = "STARTED"           # Chauffeur a démarré -> VERROUILLAGE (Annulation bloquée)
    COMPLETED = "COMPLETED"       # Clôturée (PIN validé si MoMo, ou validation simple si Cash)
    CANCELLED = "CANCELLED"       # Annulée (Autorisé seulement AVANT STARTED)

class RideBase(SQLModel):
    pickup_name: str = Field(description="Nom ou repère de prise en charge (ex: Carrefour EMIA)")
    dropoff_name: str = Field(description="Nom ou repère de destination (ex: Marché Mokolo)")
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    pickup_poi_id: Optional[int] = Field(default=None, foreign_key="pois.id")
    dropoff_poi_id: Optional[int] = Field(default=None, foreign_key="pois.id")
    payment_mode: PaymentMode = Field(default=PaymentMode.MOMO)
    ride_type: RideType = Field(default=RideType.SOLO)
    suggested_price: float = Field(description="Prix de base suggéré par l'application en FCFA")
    agreed_price: float = Field(description="Prix final convenu ou proposé en FCFA")

class Ride(RideBase, table=True):
    __tablename__ = "rides"
    id: Optional[int] = Field(default=None, primary_key=True)
    passenger_id: int = Field(foreign_key="users.id", index=True)
    driver_id: Optional[int] = Field(default=None, foreign_key="users.id", index=True)
    
    status: RideStatus = Field(default=RideStatus.REQUESTED, index=True)
    is_locked: bool = Field(default=False, description="True dès que le chauffeur clique 'Démarrer'. L'annulation est alors impossible.")

    # Sécurité & Escrow
    secret_pin: str = Field(
        default_factory=lambda: f"{secrets.randbelow(9000) + 1000:04d}",
        description="Code PIN oral à 4 chiffres généré pour le passager (ex: 4821)"
    )
    pin_attempts: int = Field(default=0, description="Nombre de tentatives de saisie du PIN par le chauffeur (max 3)")
    
    # Suivi temps réel & SOS
    share_token: str = Field(
        default_factory=lambda: secrets.token_urlsafe(16),
        unique=True,
        index=True,
        description="Jeton public sécurisé pour le lien de suivi web"
    )
    is_sos_active: bool = Field(default=False, description="Déclenchement alerte SOS d'urgence")
    sos_activated_at: Optional[datetime] = None

    # Covoiturage (Groupement de 2 passagers)
    shared_group_id: Optional[str] = Field(default=None, index=True, description="Identifiant du groupe de covoiturage")
    
    # Commission VORA calculée
    commission_amount: float = Field(default=0.0)

    # Dates de cycle de vie
    created_at: datetime = Field(default_factory=utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
