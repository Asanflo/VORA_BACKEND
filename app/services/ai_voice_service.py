import re
import json
from typing import Dict, Any, Optional
import httpx
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.ride import RideType
from app.schemas.ai import VoiceIntentResponse
from app.schemas.poi import POIRead
from app.services.poi_service import POIService
from app.services.pricing_service import PricingService
from app.core.config import settings

CAMEROON_NLU_SYSTEM_PROMPT = """Tu es l'assistant vocal intelligent de VORA, l'application de transport urbain au Cameroun (Yaoundé, Douala).
Tu comprends parfaitement le Français familier, le Camfranglais et le Pidgin camerounais (ex: "Drop me for Carrefour EMIA", "I wan go Mokolo", "Je sors de Total Melen je go à la Poste Centrale", "Tu me drop à la Pharmacie du Soleil").

Ta mission :
À partir de la phrase dictée par l'utilisateur, extrais au format JSON strict :
{
  "pickup_landmark": "Nom du repère de départ ou null si non mentionné",
  "dropoff_landmark": "Nom du repère de destination obligatoire",
  "ride_type": "SOLO" ou "SHARED" (SHARED si mention de partage, ramassage ou covoiturage),
  "confidence": float entre 0.0 et 1.0,
  "friendly_reply": "Message court et chaleureux en français confirmant la destination"
}
Réponds UNIQUEMENT avec le JSON valide, sans balises markdown."""

class AIVoiceService:
    @classmethod
    async def parse_voice_text(
        cls,
        session: AsyncSession,
        raw_text: str,
        user_current_lat: Optional[float] = None,
        user_current_lng: Optional[float] = None
    ) -> VoiceIntentResponse:
        """
        Analyse une requête vocale ou textuelle en français familier / Pidgin camerounais.
        Utilise l'API Groq (Llama) si disponible, ou le moteur local expert en cas de fonctionnement hors-ligne.
        """
        clean_text = raw_text.strip()
        parsed_data = None

        # 1. Tentative avec Groq API si clé configurée
        if settings.GROQ_API_KEY:
            try:
                parsed_data = await cls._call_groq_api(clean_text)
            except Exception as e:
                # Bascule transparente sur le parseur local
                parsed_data = None

        # 2. Parseur local intelligent de repli (Offline Fallback)
        if not parsed_data:
            parsed_data = cls._local_cameroon_nlu_parser(clean_text)

        pickup_text = parsed_data.get("pickup_landmark")
        dropoff_text = parsed_data.get("dropoff_landmark")
        ride_type_str = parsed_data.get("ride_type", "SOLO")
        ride_type = RideType.SHARED if ride_type_str == "SHARED" else RideType.SOLO
        confidence = float(parsed_data.get("confidence", 0.85))

        # 3. Résolution des repères dans la base de données locale VORA
        matched_pickup_poi: Optional[POIRead] = None
        matched_dropoff_poi: Optional[POIRead] = None

        if dropoff_text:
            dropoff_results = await POIService.search_pois(session, dropoff_text, limit=1)
            if dropoff_results:
                matched_dropoff_poi = dropoff_results[0]

        if pickup_text:
            pickup_results = await POIService.search_pois(session, pickup_text, limit=1)
            if pickup_results:
                matched_pickup_poi = pickup_results[0]
        elif user_current_lat and user_current_lng:
            nearest = await POIService.find_nearest_poi(session, user_current_lat, user_current_lng)
            if nearest:
                matched_pickup_poi = nearest.poi

        if not matched_pickup_poi:
            default_pois = await POIService.search_pois(session, "Poste Centrale", limit=1)
            if default_pois:
                matched_pickup_poi = default_pois[0]

        # 4. Calcul du tarif estimé
        suggested_price = 1000.0
        if matched_pickup_poi and matched_dropoff_poi:
            estimate = await PricingService.estimate_ride(
                session,
                matched_pickup_poi.latitude, matched_pickup_poi.longitude,
                matched_dropoff_poi.latitude, matched_dropoff_poi.longitude,
                ride_type=ride_type
            )
            suggested_price = estimate.suggested_price_shared if ride_type == RideType.SHARED else estimate.suggested_price_solo

        # 5. Construction de la réponse vocale d'accompagnement
        dest_name = matched_dropoff_poi.name if matched_dropoff_poi else (dropoff_text or "votre destination")
        orig_name = matched_pickup_poi.name if matched_pickup_poi else "votre position"

        reply = (
            f"C'est bien noté ! Trajet de {orig_name} vers {dest_name} en mode "
            f"{'covoiturage partagé' if ride_type == RideType.SHARED else 'course solo'}. "
            f"Tarif conseillé : {suggested_price:.0f} FCFA."
        )

        return VoiceIntentResponse(
            raw_input=clean_text,
            pickup_landmark=matched_pickup_poi.name if matched_pickup_poi else pickup_text,
            dropoff_landmark=matched_dropoff_poi.name if matched_dropoff_poi else dropoff_text,
            ride_type=ride_type,
            confidence=confidence,
            pickup_poi=matched_pickup_poi,
            dropoff_poi=matched_dropoff_poi,
            suggested_price_fcfa=suggested_price,
            assistant_reply=reply
        )

    @classmethod
    async def _call_groq_api(cls, text: str) -> Optional[Dict[str, Any]]:
        """Appel à l'API Groq (Llama), gratuite et compatible OpenAI"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": CAMEROON_NLU_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                content_clean = re.sub(r"^```json\s*", "", content.strip())
                content_clean = re.sub(r"\s*```$", "", content_clean)
                return json.loads(content_clean)
        return None

    @classmethod
    def _local_cameroon_nlu_parser(cls, text: str) -> Dict[str, Any]:
        """
        Moteur NLU local spécialisé pour le Français familier et le Pidgin camerounais :
        - 'Drop me for Carrefour EMIA'
        - 'Carry me go Marché Mokolo'
        - 'I wan go Pharmacie du Soleil'
        - 'Je monte à Total Melen pour descendre à Poste Centrale'
        - 'Tu me drop au Carrefour EMIA'
        - 'Je want go for Bastos'
        """
        text_lower = text.lower().strip()

        ride_type = "SOLO"
        if any(w in text_lower for w in ["partag", "covoiturage", "ramassage", "share", "together"]):
            ride_type = "SHARED"

        pickup_landmark = None
        dropoff_landmark = None

        two_points_match = re.search(
            r"(?:de|depuis|je sors de|je quitte|i dey for|from)\s+([a-z0-9\s\-éèêîïàç]+?)\s+(?:vers|pour|go|to|à|pour descendre à|carry me go|take me to)\s+([a-z0-9\s\-éèêîïàç]+)",
            text_lower
        )
        if two_points_match:
            pickup_landmark = two_points_match.group(1).strip()
            dropoff_landmark = two_points_match.group(2).strip()

        if not dropoff_landmark:
            pidgin_match = re.search(r"(?:drop me for|carry me go|i wan go|take me to|leave me for|drop me at)\s+([a-z0-9\s\-éèêîïàç]+)", text_lower)
            if pidgin_match:
                dropoff_landmark = pidgin_match.group(1).strip()

        if not dropoff_landmark:
            fr_match = re.search(r"(?:tu me drop à|tu me drop au|laisse-moi au|laisse moi à|je vais au|je vais à|je go au|je go à|direction|destination|pour aller à|pour aller au)\s+([a-z0-9\s\-éèêîïàç]+)", text_lower)
            if fr_match:
                dropoff_landmark = fr_match.group(1).strip()

        for _ in range(3):
            if dropoff_landmark:
                dropoff_landmark = re.sub(
                    r"(?:en covoiturage|covoiturage|en partag[ée]|partag[ée]|en partage|s'il te plaît|stp|abeg|vite|rapidement|en taxi|pour taxi|taxi|now|tout de suite)$",
                    "",
                    dropoff_landmark,
                    flags=re.IGNORECASE
                ).strip()
            if pickup_landmark:
                pickup_landmark = re.sub(
                    r"(?:en covoiturage|covoiturage|en partag[ée]|partag[ée]|en partage|s'il te plaît|stp|abeg|vite|rapidement|en taxi|pour taxi|taxi|now|tout de suite)$",
                    "",
                    pickup_landmark,
                    flags=re.IGNORECASE
                ).strip()

        if not dropoff_landmark:
            dropoff_landmark = text.strip()

        return {
            "pickup_landmark": pickup_landmark,
            "dropoff_landmark": dropoff_landmark,
            "ride_type": ride_type,
            "confidence": 0.88,
            "friendly_reply": f"Direction {dropoff_landmark} comprise !"
        }