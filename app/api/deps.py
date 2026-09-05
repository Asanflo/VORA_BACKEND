from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.core.security import decode_access_token
from app.models.user import User, UserRole, DriverProfile

security_bearer = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    session: AsyncSession = Depends(get_session)
) -> Optional[User]:
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = await session.get(User, int(user_id))
    return user

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    session: AsyncSession = Depends(get_session)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'authentification manquant."
        )
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton d'authentification invalide ou expiré."
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Jeton invalide.")
    
    user = await session.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inexistant ou désactivé.")
    return user

async def get_current_driver(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> DriverProfile:
    if user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux chauffeurs VORA enregistrés."
        )
    stmt = select(DriverProfile).where(DriverProfile.user_id == user.id)
    result = await session.exec(stmt)
    driver_profile = result.first()
    if not driver_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil chauffeur non initialisé."
        )
    return driver_profile
