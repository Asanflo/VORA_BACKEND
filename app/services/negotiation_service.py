from typing import List, Tuple, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.negotiation import NegotiationOffer, OfferStatus
from app.models.ride import Ride, RideStatus
from app.models.user import User, DriverProfile
from app.schemas.negotiation import NegotiationOfferRead

class NegotiationService:
    @classmethod
    async def make_driver_offer(
        cls,
        session: AsyncSession,
        ride_id: int,
        driver_id: int,
        offered_price: float,
        driver_eta_minutes: int = 5
    ) -> Tuple[bool, str, Optional[NegotiationOffer]]:
        """Un chauffeur soumet une offre ou contre-proposition pour une course"""
        ride = await session.get(Ride, ride_id)
        if not ride:
            return False, "Course introuvable.", None

        if ride.status not in [RideStatus.REQUESTED, RideStatus.NEGOTIATING]:
            return False, f"La course n'est plus négociable (statut actuel: {ride.status}).", None

        # Vérifier si ce chauffeur a déjà fait une offre en attente
        stmt = select(NegotiationOffer).where(
            NegotiationOffer.ride_id == ride_id,
            NegotiationOffer.driver_id == driver_id,
            NegotiationOffer.status == OfferStatus.PENDING
        )
        result = await session.exec(stmt)
        existing_offer = result.first()

        if existing_offer:
            existing_offer.offered_price = offered_price
            existing_offer.driver_eta_minutes = driver_eta_minutes
            session.add(existing_offer)
            offer = existing_offer
        else:
            offer = NegotiationOffer(
                ride_id=ride_id,
                driver_id=driver_id,
                offered_price=offered_price,
                driver_eta_minutes=driver_eta_minutes,
                status=OfferStatus.PENDING
            )
            session.add(offer)

        ride.status = RideStatus.NEGOTIATING
        session.add(ride)
        await session.commit()
        await session.refresh(offer)
        return True, "Contre-offre envoyée au passager avec succès.", offer

    @classmethod
    async def accept_offer(
        cls,
        session: AsyncSession,
        ride_id: int,
        offer_id: int,
        passenger_id: int
    ) -> Tuple[bool, str, Optional[Ride]]:
        """Le passager accepte l'offre d'un chauffeur spécifique"""
        ride = await session.get(Ride, ride_id)
        if not ride:
            return False, "Course introuvable.", None

        if ride.passenger_id != passenger_id:
            return False, "Action non autorisée sur cette course.", None

        if ride.status not in [RideStatus.REQUESTED, RideStatus.NEGOTIATING]:
            return False, f"Impossible d'accepter l'offre (statut: {ride.status}).", None

        offer = await session.get(NegotiationOffer, offer_id)
        if not offer or offer.ride_id != ride_id:
            return False, "Offre introuvable pour cette course.", None

        # Valider l'offre choisie
        offer.status = OfferStatus.ACCEPTED
        session.add(offer)

        # Mettre à jour la course avec le prix et le chauffeur retenu
        ride.driver_id = offer.driver_id
        ride.agreed_price = offer.offered_price
        ride.status = RideStatus.ACCEPTED
        session.add(ride)

        # Rejeter les autres offres en attente
        stmt = select(NegotiationOffer).where(
            NegotiationOffer.ride_id == ride_id,
            NegotiationOffer.id != offer_id,
            NegotiationOffer.status == OfferStatus.PENDING
        )
        result = await session.exec(stmt)
        other_offers = result.all()
        for o in other_offers:
            o.status = OfferStatus.REJECTED
            session.add(o)

        await session.commit()
        await session.refresh(ride)
        return True, "Offre chauffeur acceptée ! Le chauffeur est en route pour vous récupérer.", ride

    @classmethod
    async def get_ride_offers(
        cls,
        session: AsyncSession,
        ride_id: int
    ) -> List[NegotiationOfferRead]:
        """Récupère toutes les offres pour une course avec les détails chauffeur"""
        stmt = select(NegotiationOffer).where(NegotiationOffer.ride_id == ride_id)
        result = await session.exec(stmt)
        offers = result.all()

        offers_read = []
        for offer in offers:
            driver_user = await session.get(User, offer.driver_id)
            driver_name = driver_user.full_name if driver_user else "Chauffeur"
            
            # Récupérer profil chauffeur
            stmt_dp = select(DriverProfile).where(DriverProfile.user_id == offer.driver_id)
            dp_res = await session.exec(stmt_dp)
            dp = dp_res.first()

            offers_read.append(
                NegotiationOfferRead(
                    id=offer.id,
                    ride_id=offer.ride_id,
                    driver_id=offer.driver_id,
                    driver_name=driver_name,
                    driver_rating=dp.rating_avg if dp else 5.0,
                    taxi_door_number=dp.taxi_door_number if dp else "N/A",
                    car_model_color=dp.car_model_color if dp else "Taxi Jaune",
                    offered_price=offer.offered_price,
                    driver_eta_minutes=offer.driver_eta_minutes,
                    status=offer.status,
                    created_at=offer.created_at
                )
            )
        return offers_read
