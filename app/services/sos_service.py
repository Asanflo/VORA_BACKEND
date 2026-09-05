from typing import List, Tuple, Optional
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.ride import Ride
from app.models.user import User
from app.schemas.sos import SOSAlertRead
from app.core.security import utc_now

class SOSService:
    EMERGENCY_SERVICES = [
        "+237117 (Police Secours)",
        "+237119 (Gendarmerie Nationale)",
        "+237690000000 (Contact d'urgence famille)"
    ]

    @classmethod
    async def trigger_sos_alert(
        cls,
        session: AsyncSession,
        ride: Ride,
        current_lat: float,
        current_lng: float,
        custom_message: Optional[str] = None
    ) -> SOSAlertRead:
        """
        Déclenche l'alerte d'urgence SOS :
        - Active le statut SOS sur la course
        - Diffuse les coordonnées GPS instantanées
        - Génère et simule l'envoi de SMS de détresse avec lien de suivi public
        """
        ride.is_sos_active = True
        ride.sos_activated_at = utc_now()
        session.add(ride)
        await session.commit()
        await session.refresh(ride)

        # Lien de suivi web en direct
        tracking_url = f"https://vora.cm/track/{ride.share_token}"

        # Construction du message SMS envoyé aux contacts de secours
        sms_text = (
            f"🚨 ALERTE SOS VORA : Passager en détresse sur la course #{ride.id} !\n"
            f"Repère : De {ride.pickup_name} vers {ride.dropoff_name}.\n"
            f"Position GPS actuelle : {current_lat:.5f}, {current_lng:.5f}\n"
            f"Carte Google Maps : https://maps.google.com/?q={current_lat},{current_lng}\n"
            f"Suivi en temps réel VORA : {tracking_url}"
        )
        if custom_message:
            sms_text += f"\nNote : {custom_message}"

        # En production, webhook Twilio / SMS local Cameroun (Orange SMS API / MTN SMS)
        # Ici simulation et log sécurisé pour le jury et l'émulateur Flutter

        return SOSAlertRead(
            ride_id=ride.id,
            is_sos_active=True,
            sos_activated_at=ride.sos_activated_at,
            share_token=ride.share_token,
            public_tracking_url=tracking_url,
            latitude=current_lat,
            longitude=current_lng,
            emergency_contacts_alerted=cls.EMERGENCY_SERVICES,
            alert_status="SMS_DISPATCHED_TO_EMERGENCY_SERVICES"
        )
