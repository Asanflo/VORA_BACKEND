import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import init_db, async_session_maker
from app.core.seed_data import seed_initial_data
from app.api.v1.router import api_v1_router
from app.api.websocket.connection_manager import manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialisation de la base de données (Supabase Postgres ou SQLite)
    await init_db()
    # Insertion des données de repères locaux camerounais et comptes de démo
    async with async_session_maker() as session:
        await seed_initial_data(session)
    # Création du dossier d'upload local si nécessaire
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "Backend FastAPI & SQLModel pour VORA : Mobilité urbaine, Taxis jaunes, "
        "Repères locaux camerounais, Séquestre Mobile Money, Covoiturage et Sécurité SOS."
    ),
    lifespan=lifespan,
    docs_url="/docs", #if settings.ENVIRONMENT != "production" else None
    redoc_url="/redoc" #if settings.ENVIRONMENT != "production" else None
)

# Configuration CORS pour Flutter (Web, iOS, Android Emulateur 10.0.2.2, Appareil Physique)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage du dossier statique pour les photos et documents de chauffeurs
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Enregistrement des routes API V1
app.include_router(api_v1_router)

# Routes WebSocket temps réel
@app.websocket("/ws/rides/{ride_id}")
async def websocket_ride_channel(websocket: WebSocket, ride_id: int):
    """Canal WebSocket dédié au suivi temps réel d'une course (offres, statuts, SOS)"""
    await manager.connect_ride(ride_id, websocket)
    try:
        while True:
            # Écoute de messages éventuels du client Flutter
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_ride(ride_id, websocket)

@app.websocket("/ws/global")
async def websocket_global_channel(websocket: WebSocket):
    """Canal WebSocket de diffusion globale (courses disponibles, positions chauffeurs)"""
    await manager.connect_global(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_global(websocket)

@app.get("/health", tags=["Santé"])
async def health_check():
    """Vérification de l'état de santé du backend"""
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

@app.get("/", tags=["Accueil"])
async def root():
    return {
        "message": "Bienvenue sur l'API VORA Backend Cameroun 🚖",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

