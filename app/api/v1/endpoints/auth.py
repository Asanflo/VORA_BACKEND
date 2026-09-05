from typing import Optional
import os
import uuid
import shutil
import json
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.core.config import settings
from app.core.security import normalize_cameroon_phone, create_access_token
from app.models.user import User, DriverProfile, UserRole, VerificationStatus
from app.schemas.auth import (
    UserLoginRequest, UserVerifyOTPRequest, PassengerRegisterRequest,
    DriverRegisterRequest, AuthResponse, UserRead, DriverProfileRead
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentification & Comptes"])

@router.post("/login", summary="Demande de connexion par téléphone (Envoi OTP)")
async def login_request(req: UserLoginRequest, session: AsyncSession = Depends(get_session)):
    """
    Initie la connexion avec un numéro de téléphone camerounais (+237 6XXXXXXXX).
    En mode démo/hackathon, le code OTP généré par défaut est '1234'.
    """
    phone = normalize_cameroon_phone(req.phone_number)
    stmt = select(User).where(User.phone_number == phone)
    result = await session.exec(stmt)
    user = result.first()

    return {
        "success": True,
        "phone_number": phone,
        "is_registered": user is not None,
        "role": user.role if user else None,
        "message": "Code OTP envoyé par SMS (Code démo : 1234)"
    }

@router.post("/verify-otp", response_model=AuthResponse, summary="Validation de l'OTP et émission du token JWT")
async def verify_otp(req: UserVerifyOTPRequest, session: AsyncSession = Depends(get_session)):
    """Valide le code OTP et connecte l'utilisateur"""
    phone = normalize_cameroon_phone(req.phone_number)
    
    # Validation du code OTP (Démo : 1234 ou 4 chiffres)
    if req.otp_code != "1234" and len(req.otp_code) != 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code OTP invalide.")

    stmt = select(User).where(User.phone_number == phone)
    result = await session.exec(stmt)
    user = result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Numéro non enregistré. Veuillez d'abord créer votre compte passager ou chauffeur."
        )

    # Récupérer profil chauffeur si applicable
    driver_read = None
    if user.role == UserRole.DRIVER:
        stmt_dp = select(DriverProfile).where(DriverProfile.user_id == user.id)
        dp_res = await session.exec(stmt_dp)
        dp = dp_res.first()
        if dp:
            driver_read = DriverProfileRead(
                id=dp.id,
                user_id=dp.user_id,
                cni_number=dp.cni_number,
                driver_license_number=dp.driver_license_number,
                taxi_door_number=dp.taxi_door_number,
                vehicle_plate=dp.vehicle_plate,
                car_model_color=dp.car_model_color,
                verification_status=dp.verification_status,
                rating_avg=dp.rating_avg,
                rides_completed_count=dp.rides_completed_count,
                badges=dp.badges,
                wallet_balance=dp.wallet_balance,
                cni_document_url=dp.cni_document_url,
                driver_license_document_url=dp.driver_license_document_url,
                vehicle_registration_doc_url=dp.vehicle_registration_doc_url
            )

    token = create_access_token({"sub": str(user.id), "role": user.role, "phone": user.phone_number})
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead(
            id=user.id,
            phone_number=user.phone_number,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        ),
        driver_profile=driver_read
    )

@router.post("/passenger/register", response_model=AuthResponse, summary="Inscription d'un nouveau Passager")
async def register_passenger(req: PassengerRegisterRequest, session: AsyncSession = Depends(get_session)):
    """Création d'un compte passager VORA"""
    phone = normalize_cameroon_phone(req.phone_number)
    stmt = select(User).where(User.phone_number == phone)
    result = await session.exec(stmt)
    if result.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce numéro de téléphone est déjà utilisé.")

    user = User(
        phone_number=phone,
        full_name=req.full_name,
        role=UserRole.PASSENGER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role, "phone": user.phone_number})
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead(
            id=user.id,
            phone_number=user.phone_number,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        )
    )

@router.post("/driver/register", response_model=AuthResponse, summary="Inscription Chauffeur avec pièces justificatives obligatoires")
async def register_driver(req: DriverRegisterRequest, session: AsyncSession = Depends(get_session)):
    """
    Création d'un compte Chauffeur de Taxi Jaune.
    Exige obligatoirement : CNI, Permis de conduire, Numéro de portière de taxi jaune et Immatriculation.
    """
    phone = normalize_cameroon_phone(req.phone_number)
    stmt = select(User).where(User.phone_number == phone)
    result = await session.exec(stmt)
    if result.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce numéro de téléphone est déjà enregistré.")

    # Vérifier l'unicité du numéro de portière communal du taxi jaune
    stmt_door = select(DriverProfile).where(DriverProfile.taxi_door_number == req.taxi_door_number.strip().upper())
    res_door = await session.exec(stmt_door)
    if res_door.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Le numéro de portière '{req.taxi_door_number}' est déjà enregistré."
        )

    # Création du compte utilisateur
    user = User(
        phone_number=phone,
        full_name=req.full_name,
        role=UserRole.DRIVER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Création du profil chauffeur avec pièces justificatives
    profile = DriverProfile(
        user_id=user.id,
        cni_number=req.cni_number.strip(),
        cni_document_url=req.cni_document_url,
        driver_license_number=req.driver_license_number.strip(),
        driver_license_document_url=req.driver_license_document_url,
        vehicle_registration_doc_url=req.vehicle_registration_doc_url,
        taxi_door_number=req.taxi_door_number.strip().upper(),
        vehicle_plate=req.vehicle_plate.strip().upper(),
        car_model_color=req.car_model_color.strip(),
        verification_status=VerificationStatus.PENDING_VERIFICATION,
        badges_json=json.dumps(["NOUVEAU_CHAUFFEUR", "EN_ATTENTE_VALIDATION"]),
        rating_avg=5.0,
        rides_completed_count=0,
        wallet_balance=0.0
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)

    token = create_access_token({"sub": str(user.id), "role": user.role, "phone": user.phone_number})
    
    driver_read = DriverProfileRead(
        id=profile.id,
        user_id=profile.user_id,
        cni_number=profile.cni_number,
        driver_license_number=profile.driver_license_number,
        taxi_door_number=profile.taxi_door_number,
        vehicle_plate=profile.vehicle_plate,
        car_model_color=profile.car_model_color,
        verification_status=profile.verification_status,
        rating_avg=profile.rating_avg,
        rides_completed_count=profile.rides_completed_count,
        badges=profile.badges,
        wallet_balance=profile.wallet_balance,
        cni_document_url=profile.cni_document_url,
        driver_license_document_url=profile.driver_license_document_url,
        vehicle_registration_doc_url=profile.vehicle_registration_doc_url
    )

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead(
            id=user.id,
            phone_number=user.phone_number,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        ),
        driver_profile=driver_read
    )

@router.post("/driver/upload-document", summary="Téléversement d'une pièce justificative (CNI, Permis, Carte grise)")
async def upload_driver_document(
    document_type: str = Form(..., description="cni, permis, ou carte_grise"),
    file: UploadFile = File(...)
):
    """
    Téléversement direct d'un fichier photo ou PDF pour les pièces chauffeur.
    Stocke dans le dossier uploads ou Supabase Storage et retourne l'URL publique.
    """
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"{document_type}_{uuid.uuid4().hex[:12]}{extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_url = f"/uploads/{unique_filename}"
    return {
        "success": True,
        "document_type": document_type,
        "filename": unique_filename,
        "document_url": file_url
    }

@router.get("/me", response_model=AuthResponse, summary="Profil de l'utilisateur connecté")
async def get_me(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    """Retourne les informations du compte connecté et du profil chauffeur le cas échéant"""
    driver_read = None
    if user.role == UserRole.DRIVER:
        stmt_dp = select(DriverProfile).where(DriverProfile.user_id == user.id)
        dp_res = await session.exec(stmt_dp)
        dp = dp_res.first()
        if dp:
            driver_read = DriverProfileRead(
                id=dp.id,
                user_id=dp.user_id,
                cni_number=dp.cni_number,
                driver_license_number=dp.driver_license_number,
                taxi_door_number=dp.taxi_door_number,
                vehicle_plate=dp.vehicle_plate,
                car_model_color=dp.car_model_color,
                verification_status=dp.verification_status,
                rating_avg=dp.rating_avg,
                rides_completed_count=dp.rides_completed_count,
                badges=dp.badges,
                wallet_balance=dp.wallet_balance,
                cni_document_url=dp.cni_document_url,
                driver_license_document_url=dp.driver_license_document_url,
                vehicle_registration_doc_url=dp.vehicle_registration_doc_url
            )

    token = create_access_token({"sub": str(user.id), "role": user.role, "phone": user.phone_number})
    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserRead(
            id=user.id,
            phone_number=user.phone_number,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active
        ),
        driver_profile=driver_read
    )
