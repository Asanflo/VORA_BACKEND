from typing import Tuple, Optional
from datetime import datetime
import uuid
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.escrow import EscrowTransaction, EscrowStatus, PaymentProvider
from app.models.ride import Ride, RideStatus, PaymentMode
from app.models.user import DriverProfile
from app.core.config import settings
from app.core.security import utc_now

class PaymentAggregatorService:
    """
    Interface pour l'agrégateur de paiement gérant le séquestre Mobile Money (MTN MoMo & Orange Money).
    Supporte un mode Sandbox/Mock pour les démonstrations de hackathon et tests unitaires,
    ainsi que l'architecture pour les agrégateurs réels (Campay / NotchPay / CinetPay).
    """

    @classmethod
    async def create_escrow_hold(
        cls,
        session: AsyncSession,
        ride: Ride,
        passenger_phone: str,
        amount: float,
        provider: PaymentProvider = PaymentProvider.MTN_MOMO
    ) -> EscrowTransaction:
        """
        Étape 1 : Pré-autorisation & Blocage.
        L'argent est prélevé et gelé sur le compte séquestre de l'agrégateur.
        """
        # Calcul de la commission VORA et du montant net chauffeur
        commission = round(amount * (settings.VORA_COMMISSION_PERCENTAGE / 100.0), 2)
        driver_net = round(amount - commission, 2)

        # Génération d'une référence d'agrégateur unique
        aggregator_ref = f"ESCROW-MOMO-{uuid.uuid4().hex[:10].upper()}"

        transaction = EscrowTransaction(
            ride_id=ride.id,
            passenger_phone=passenger_phone,
            amount=amount,
            commission_amount=commission,
            driver_net_amount=driver_net,
            provider=provider,
            aggregator_reference=aggregator_ref,
            status=EscrowStatus.HELD,
            held_at=utc_now()
        )
        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)
        return transaction

    @classmethod
    async def release_escrow_with_pin(
        cls,
        session: AsyncSession,
        ride: Ride,
        entered_pin: str,
        driver_phone: str
    ) -> Tuple[bool, str, Optional[EscrowTransaction]]:
        """
        Étape 5 : Libération des fonds du séquestre vers le MoMo du chauffeur
        uniquement après validation du code PIN oral à 4 chiffres dicté par le passager.
        Règle d'arrêt : Max 3 tentatives avant blocage de sécurité.
        """
        if ride.status != RideStatus.STARTED:
            return False, f"Impossible de libérer le séquestre : la course a le statut '{ride.status}'. Elle doit être démarrée.", None

        if ride.payment_mode != PaymentMode.MOMO:
            return False, "Cette course n'utilise pas le séquestre Mobile Money.", None

        # Récupération de la transaction de séquestre
        stmt = select(EscrowTransaction).where(EscrowTransaction.ride_id == ride.id)
        result = await session.exec(stmt)
        transaction = result.first()

        if not transaction:
            return False, "Aucune transaction de séquestre trouvée pour cette course.", None

        if transaction.status == EscrowStatus.RELEASED:
            return False, "Les fonds ont déjà été libérés pour cette course.", transaction

        # Protection contre la force brute (Max 3 tentatives)
        if ride.pin_attempts >= 3:
            return False, "Code PIN bloqué après 3 tentatives incorrectes. Veuillez contacter le support VORA.", transaction

        # Vérification du code PIN oral
        if ride.secret_pin != entered_pin.strip():
            ride.pin_attempts += 1
            session.add(ride)
            await session.commit()
            remaining = 3 - ride.pin_attempts
            return False, f"Code PIN oral incorrect ({remaining} tentative(s) restante(s)).", transaction

        # Succès : Libération instantanée des fonds du séquestre de l'agrégateur
        transaction.status = EscrowStatus.RELEASED
        transaction.driver_phone = driver_phone
        transaction.released_at = utc_now()
        session.add(transaction)

        # Clôture de la course
        ride.status = RideStatus.COMPLETED
        ride.completed_at = utc_now()
        session.add(ride)

        await session.commit()
        await session.refresh(transaction)
        await session.refresh(ride)

        return True, "Code PIN validé avec succès ! Fonds séquestrés libérés instantanément vers le compte MoMo du chauffeur.", transaction

    @classmethod
    async def refund_escrow(
        cls,
        session: AsyncSession,
        ride: Ride
    ) -> Tuple[bool, str, Optional[EscrowTransaction]]:
        """
        Remboursement des fonds au passager si la course est annulée AVANT d'être démarrée.
        Règle d'arrêt : Une course 'STARTED' (verrouillée) ne peut PAS être annulée.
        """
        if ride.is_locked or ride.status == RideStatus.STARTED:
            return False, "Impossible d'annuler : la course est verrouillée car le chauffeur a déjà démarré le trajet.", None

        stmt = select(EscrowTransaction).where(EscrowTransaction.ride_id == ride.id)
        result = await session.exec(stmt)
        transaction = result.first()

        if transaction and transaction.status == EscrowStatus.HELD:
            transaction.status = EscrowStatus.REFUNDED
            transaction.refunded_at = utc_now()
            session.add(transaction)

        ride.status = RideStatus.CANCELLED
        ride.cancelled_at = utc_now()
        session.add(ride)

        await session.commit()
        if transaction:
            await session.refresh(transaction)
        await session.refresh(ride)

        return True, "Course annulée. Les fonds du séquestre ont été intégralement remboursés sur le Mobile Money du passager.", transaction

    @classmethod
    async def process_cash_completion(
        cls,
        session: AsyncSession,
        ride: Ride,
        driver_profile: Optional[DriverProfile]
    ) -> Tuple[bool, str]:
        """
        Scénario Espèces (Cash) :
        À destination, le passager remet le cash en main propre.
        Le chauffeur clique simplement sur 'Valider / Terminer la course'.
        La course est clôturée et la commission VORA est déduite du solde portefeuille du chauffeur.
        """
        if ride.status != RideStatus.STARTED:
            return False, f"Impossible de terminer : la course doit avoir le statut 'STARTED' (actuel: {ride.status})."

        commission = round(ride.agreed_price * (settings.VORA_COMMISSION_PERCENTAGE / 100.0), 2)
        ride.commission_amount = commission
        ride.status = RideStatus.COMPLETED
        ride.completed_at = utc_now()
        session.add(ride)

        if driver_profile:
            # Déduction de la commission sur le portefeuille chauffeur
            driver_profile.wallet_balance -= commission
            driver_profile.rides_completed_count += 1
            session.add(driver_profile)

        await session.commit()
        await session.refresh(ride)
        return True, f"Course en espèces validée avec succès. Commission VORA de {commission:.0f} FCFA déduite."
