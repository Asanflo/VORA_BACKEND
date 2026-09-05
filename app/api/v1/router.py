from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, poi, rides, negotiation, escrow,
    sos, tracking, ai_assistant, weather_alerts, drivers
)

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth.router)
api_v1_router.include_router(poi.router)
api_v1_router.include_router(rides.router)
api_v1_router.include_router(negotiation.router)
api_v1_router.include_router(escrow.router)
api_v1_router.include_router(sos.router)
api_v1_router.include_router(tracking.router)
api_v1_router.include_router(ai_assistant.router)
api_v1_router.include_router(weather_alerts.router)
api_v1_router.include_router(drivers.router)
