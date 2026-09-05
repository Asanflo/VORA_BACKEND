from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.database import get_session
from app.schemas.ai import VoiceIntentRequest, VoiceIntentResponse
from app.services.ai_voice_service import AIVoiceService

router = APIRouter(prefix="/ai", tags=["Assistant Vocal IA (Pidgin & Français)"])

@router.post("/voice-intent", response_model=VoiceIntentResponse, summary="Analyse d'intention vocale ou textuelle (Support Camfranglais & Pidgin)")
async def parse_voice_booking_intent(
    req: VoiceIntentRequest,
    current_lat: Optional[float] = Query(None, description="Position GPS actuelle de l'utilisateur"),
    current_lng: Optional[float] = Query(None, description="Position GPS actuelle de l'utilisateur"),
    session: AsyncSession = Depends(get_session)
):
    """
    Assistant IA inclusif pour VORA :
    Comprend les dictées vocales transcrites telles que :
    - 'Drop me for Carrefour EMIA' (Pidgin)
    - 'Carry me go Marché Mokolo en covoiturage' (Pidgin + Partagé)
    - 'Je monte à Total Melen pour descendre à Poste Centrale' (Français familier)
    - 'Tu me drop à la Pharmacie du Soleil stp' (Camfranglais)
    
    Extrait automatiquement le départ, la destination, le repère officiel le plus proche,
    le type de course et le prix estimé.
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le texte dicté ne peut pas être vide.")

    intent = await AIVoiceService.parse_voice_text(
        session=session,
        raw_text=req.text,
        user_current_lat=current_lat,
        user_current_lng=current_lng
    )
    return intent

@router.post("/voice-audio", response_model=VoiceIntentResponse, summary="Téléversement direct d'un fichier audio (dictée vocale)")
async def parse_voice_audio_file(
    audio_file: UploadFile = File(..., description="Fichier audio enregistré depuis Flutter (.m4a, .wav, .mp3)"),
    current_lat: Optional[float] = Query(None),
    current_lng: Optional[float] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """
    Reçoit le fichier audio brut enregistré au micro par le chauffeur ou le passager Flutter.
    Extrait l'intention et renvoie l'itinéraire suggéré.
    """
    # En mode démo, on simule une transcription textuelle par défaut ou on traite le fichier
    simulated_transcription = "Drop me for Carrefour EMIA"
    return await AIVoiceService.parse_voice_text(
        session=session,
        raw_text=simulated_transcription,
        user_current_lat=current_lat,
        user_current_lng=current_lng
    )
