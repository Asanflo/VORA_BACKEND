from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.models.escrow import EscrowTransaction, EscrowStatus
from app.models.user import User
from app.schemas.escrow import EscrowRead
from app.api.deps import get_current_user

router = APIRouter(prefix="/escrow", tags=["Paiement Séquestre Mobile Money"])

@router.get("/ride/{ride_id}", response_model=EscrowRead, summary="État du séquestre d'une course")
async def get_escrow_details(
    ride_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Consulter le statut du gel des fonds (HELD, RELEASED, REFUNDED)"""
    stmt = select(EscrowTransaction).where(EscrowTransaction.ride_id == ride_id)
    result = await session.exec(stmt)
    escrow = result.first()
    if not escrow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune transaction séquestre associée à cette course."
        )
    return EscrowRead(
        id=escrow.id,
        ride_id=escrow.ride_id,
        amount=escrow.amount,
        commission_amount=escrow.commission_amount,
        driver_net_amount=escrow.driver_net_amount,
        provider=escrow.provider,
        aggregator_reference=escrow.aggregator_reference,
        status=escrow.status,
        held_at=escrow.held_at,
        released_at=escrow.released_at,
        refunded_at=escrow.refunded_at
    )

@router.post("/webhook", summary="Webhook de retour de l'agrégateur de paiement")
async def aggregator_webhook(request: Request, session: AsyncSession = Depends(get_session)):
    """
    Endpoint de rappel pour les agrégateurs Mobile Money (Campay, NotchPay, CinetPay).
    Traite les confirmations asynchrones de paiement ou de remboursement.
    """
    body = await request.json()
    reference = body.get("reference") or body.get("transaction_id")
    event_status = body.get("status")

    if reference:
        stmt = select(EscrowTransaction).where(EscrowTransaction.aggregator_reference == reference)
        res = await session.exec(stmt)
        tx = res.first()
        if tx:
            if event_status == "SUCCESSFUL" and tx.status == EscrowStatus.PENDING_HOLD:
                tx.status = EscrowStatus.HELD
                session.add(tx)
                await session.commit()

    return {"received": True}
