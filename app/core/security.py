from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
import secrets
import re
from app.core.config import settings

def utc_now() -> datetime:
    """Retourne la date/heure UTC actuelle sans fuseau horaire (compatible SQLite/Postgres)"""
    return datetime.now(timezone.utc).replace(tzinfo=None)

def normalize_cameroon_phone(phone: str) -> str:
    """
    Normalise les numéros camerounais (Orange & MTN):
    Formats acceptés: 699000000, 237699000000, +237699000000, 6 99 00 00 00
    Résultat: +237699000000
    """
    cleaned = re.sub(r"[\s\-\.\(\)]", "", phone)
    if cleaned.startswith("+237"):
        return cleaned
    if cleaned.startswith("237") and len(cleaned) == 12:
        return f"+{cleaned}"
    if len(cleaned) == 9 and cleaned.startswith("6"):
        return f"+237{cleaned}"
    return phone

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Génère un jeton d'accès JWT pour l'authentification Flutter"""
    to_encode = data.copy()
    now = utc_now()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Décode et vérifie la validité d'un JWT"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None

def generate_oral_pin() -> str:
    """Génère un code PIN oral à 4 chiffres à dicter par le passager (ex: 4921)"""
    return f"{secrets.randbelow(9000) + 1000:04d}"

def generate_share_token() -> str:
    """Génère un jeton sécurisé pour le lien de suivi web public en direct"""
    return secrets.token_urlsafe(16)
