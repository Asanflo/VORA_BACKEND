# 🚖 VORA Mobility Backend (FastAPI + SQLModel + SupaBase)

Backend complet et performant conçu pour alimenter l'application mobile Flutter de **VORA**, la plateforme de mobilité urbaine et de covoiturage en taxi jaune adaptée aux réalités du Cameroun (Yaoundé, Douala, Bafoussam, etc.).

---

## 🌟 Les 8 Piliers Fonctionnels Implémentés

| # | Fonctionnalité | Problème Résolu | Solution Apportée dans le Backend |
|---|---|---|---|
| **1** | **Géolocalisation par Repères Locaux** | Absence de noms de rues précis et imprécisions GPS | Moteur de recherche et reverse geocoding sur 18+ repères populaires (*Carrefour EMIA, Marché Mokolo, Pharmacie du Soleil, Rond-point Deido, etc.*) avec gestion d'alias et scores de popularité. |
| **2** | **Paiement par Séquestre (Escrow) + PIN Oral** | Escroqueries, impayés, insécurité dans la rue | Intégration agrégateur Mobile Money (MTN MoMo & Orange Money). Pré-autorisation et gel des fonds à la commande. Déblocage instantané uniquement sur saisie du code PIN dicté oralement par le passager à destination. |
| **3** | **Covoiturage & Dépôt Partagé en Taxi Jaune** | Coût élevé des courses privées pour les étudiants/travailleurs | Algorithme de correspondance de corridors pour regrouper 2 passagers sur un trajet similaire. Réduction de ~35% pour chaque passager et gain accru pour le chauffeur. |
| **4** | **Tarif Flexible & Système de Négociation** | Rigidité des prix face aux habitudes locales camerounaises | Calcul d'un tarif conseillé avec possibilité pour le passager d'ajuster son offre et pour les chauffeurs d'émettre des contre-propositions en temps réel via WebSockets. |
| **5** | **Mode SOS & Partage de Trajet en Temps Réel** | Insécurité nocturne ou dans les zones isolées | Déclenchement d'urgence SOS avec broadcast de la position GPS, notification simulée aux services de secours, et génération d'un lien web public sécurisé (`/track/{share_token}`) consultable sans compte par les proches. |
| **6** | **Assistant Vocal IA (Français Familier & Pidgin)** | Difficulté de saisie au volant ou en mobilité | NLU propulsé par l'API Google Gemini avec repli local hors-ligne capable d'extraire départ, arrivée et tarif depuis des phrases en Pidgin (*"Drop me for Carrefour EMIA"*, *"Carry me go Mokolo"*) ou Camfranglais (*"Tu me drop à la Pharmacie du Soleil"*). |
| **7** | **Alertes Météo & État de la Route** | Inondations soudaines, pluies torrentielles et nids-de-poule | Détection des zones sinistrées (ex: Carrefour Warda, Ndokoti), affichage de badges d'alerte pour la carte Flutter et calcul dynamique d'une majoration incitative pour motiver les chauffeurs. |
| **8** | **Badge "Chauffeur Vérifié" & Profil de Confiance** | Faux taxis, manque de transparence | Soumission obligatoire des pièces à l'inscription (CNI, Permis, Carte Grise, **Numéro de portière de Taxi Jaune** ex: *YDE-1420*), système de validation et badges de confiance affichés sur la fiche chauffeur. |

---

## 🔄 Règles d'Arrêt & Scénarios de Paiement

### Scénario 1 : Mobile Money (Séquestre & Code PIN Oral)
1. **Passager réserve** $\rightarrow$ Les fonds sont pré-autorisés et gelés sur le compte séquestre de l'agrégateur (`status = HELD`).
2. **Chauffeur accepte** $\rightarrow$ Course assignée (`status = ACCEPTED`).
3. **Chauffeur clique "Démarrer la course"** $\rightarrow$ **Verrouillage absolu** (`is_locked = True`). Le bouton "Annuler" disparaît sur le téléphone du passager.
4. **Arrivée à destination** $\rightarrow$ Le passager dicte oralement son code PIN secret à 4 chiffres (sans sortir son téléphone).
5. **Chauffeur saisit le PIN** $\rightarrow$ Fin de course : Libération instantanée des fonds séquestrés vers le MoMo du chauffeur.

### Scénario 2 : Espèces (Cash)
1. **Passager sélectionne "Espèces"** $\rightarrow$ Réservation directe sans séquestre préalable.
2. **Chauffeur accepte** $\rightarrow$ En route vers le passager.
3. **Chauffeur clique "Démarrer la course"** $\rightarrow$ **Verrouillage absolu** (`is_locked = True`). L'annulation est bloquée.
4. **Arrivée à destination** $\rightarrow$ Remise des billets/pièces en main propre.
5. **Chauffeur clique "Valider / Terminer la course"** $\rightarrow$ Clôture immédiate et déduction automatique de la commission VORA sur le portefeuille du chauffeur.

---

## 🛠️ Stack Technique

- **Framework** : [FastAPI](https://fastapi.tiangolo.com/) (Asynchrone, rapide, documentation Swagger OpenAPI native).
- **ORM & Validation** : [SQLModel](https://sqlmodel.tiangolo.com/) (fusionne SQLAlchemy 2.0 et Pydantic v2 en un seul schéma).
- **Base de Données** : [SupaBase](https://supabase.com/) (PostgreSQL avec `asyncpg`) et SQLite asynchrone (`aiosqlite`) pour le développement local et les tests.
- **Temps Réel** : WebSockets (`/ws/rides/{ride_id}` et `/ws/global`).
- **IA** : Google Gemini API (modèle `gemini-2.5-flash`) avec moteur NLU local de secours pour le Camfranglais et le Pidgin.
- **Sécurité** : JWT (HS256), jetons de partage cryptographiques, protection anti-brute-force sur le PIN oral (max 3 tentatives).

---

## 📁 Architecture du Projet

```
Vora_Backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py            # Inscription Passager/Chauffeur (documents CNI, Permis, Portière)
│   │   │   │   ├── poi.py             # Repères populaires et reverse geocoding
│   │   │   │   ├── rides.py           # Cycle de vie, séquestre MoMo vs Cash, verrouillage
│   │   │   │   ├── negotiation.py     # Offres et contre-propositions de tarif
│   │   │   │   ├── escrow.py          # Transactions séquestre et webhooks
│   │   │   │   ├── sos.py             # Mode SOS d'urgence
│   │   │   │   ├── tracking.py        # Suivi public sans authentification (share token)
│   │   │   │   ├── ai_assistant.py    # Assistant vocal Pidgin / Français familier
│   │   │   │   ├── weather_alerts.py  # Badges zones inondées et nids-de-poule
│   │   │   │   └── drivers.py         # Fiche profil de confiance, badges et position GPS
│   │   │   └── router.py              # Routeur central v1
│   │   ├── websocket/
│   │   │   └── connection_manager.py  # WebSockets pour notifications et live tracking
│   │   └── deps.py                    # Dépendances de sécurité et rôles JWT
│   ├── core/
│   │   ├── config.py                  # Pydantic Settings
│   │   ├── database.py                # SQLModel Async Engine (Supabase / SQLite)
│   │   ├── security.py                # JWT, normalisation téléphones camerounais (+237)
│   │   └── seed_data.py               # 18+ repères Yaoundé/Douala, alertes météo et comptes test
│   ├── models/                        # Modèles SQLModel (Tables DB + Pydantic)
│   │   ├── user.py                    # Utilisateurs et profil chauffeur avec pièces
│   │   ├── poi.py                     # Repères locaux camerounais
│   │   ├── ride.py                    # Courses avec PIN et verrouillage
│   │   ├── escrow.py                  # Séquestre agrégateur Mobile Money
│   │   ├── negotiation.py             # Offres tarifaires chauffeurs
│   │   └── weather.py                 # Alertes météo et voirie
│   ├── schemas/                       # DTOs pour requêtes et réponses Flutter
│   ├── services/                      # Logique métier découplée
│   │   ├── aggregator_service.py      # Client séquestre (Hold / Release PIN / Refund / Cash)
│   │   ├── poi_service.py             # Algorithmes de recherche de repères locaux
│   │   ├── pricing_service.py         # Tarification urbaine, réduction covoiturage, surtaxe pluie
│   │   ├── shared_ride_service.py     # Correspondance automatique des trajets partagés
│   │   ├── negotiation_service.py     # Gestion des offres tarifaires
│   │   ├── sos_service.py             # Urgences et simulation SMS de détresse
│   │   ├── weather_service.py         # Détection d'alertes sur itinéraire
│   │   └── ai_voice_service.py        # Gemini API et NLU local Pidgin
│   └── main.py                        # Application FastAPI, CORS Flutter, WebSockets
├── tests/                             # Suite complète de 11 tests automatisés pytest
│   ├── conftest.py
│   ├── test_auth_driver.py
│   ├── test_poi.py
│   ├── test_escrow_pin_momo.py
│   ├── test_cash_workflow.py
│   ├── test_negotiation.py
│   ├── test_shared_rides.py
│   ├── test_sos.py
│   ├── test_ai_voice.py
│   └── test_weather.py
├── requirements.txt
├── .env.example
├── .env
└── README.md
```

---

## 🚀 Installation & Démarrage

### 1. Prérequis
- Python 3.11+ (testé et validé sur Python 3.14).

### 2. Configuration de l'environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration de SupaBase (.env)
Copiez `.env.example` vers `.env` et renseignez votre URI Supabase :
```env
# Connexion PostgreSQL SupaBase (Pooler ou Direct)
DATABASE_URL="postgresql+asyncpg://postgres:[VOTRE_MOT_DE_PASSE]@db.[VOTRE_PROJET].supabase.co:5432/postgres"

# En local sans réseau ou pour les tests rapides, SQLite async est utilisé par défaut :
# DATABASE_URL="sqlite+aiosqlite:///./vora.db"

# Clé API Google Gemini (Optionnel, un moteur local prend le relais si vide)
GEMINI_API_KEY="AIzaSy..."
```

### 4. Lancer le serveur backend
```bash
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Le serveur sera disponible sur :
- **Documentation Swagger UI interactive** : [http://localhost:8000/docs](http://localhost:8000/docs)
- **Documentation Redoc** : [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Vérification de santé** : [http://localhost:8000/health](http://localhost:8000/health)

### 5. Exécuter la suite de tests
```bash
PYTHONPATH=. ./venv/bin/pytest -v
```
Résultat : **11 tests unitaires et d'intégration validés à 100%**.

---

## 📱 Guide d'Intégration pour l'Équipe Flutter

### A. Adresses de Connexion selon l'Environnement Flutter
- **Émulateur Android** : `http://10.0.2.2:8000`
- **Simulateur iOS / Web** : `http://localhost:8000`
- **Smartphone Physique sur le même Wi-Fi** : `http://VOTRE_IP_LOCALE:8000` (ex: `http://192.168.1.45:8000`)

### B. Authentification & Comptes
- **Passager** : `POST /api/v1/auth/passenger/register`
- **Chauffeur avec Pièces** : `POST /api/v1/auth/driver/register`
  - Requis : `cni_number`, `driver_license_number`, `taxi_door_number` (ex: `YDE-1420`), `vehicle_plate` (ex: `CE 789 AA`), `car_model_color`.
  - Téléversement photos pièces : `POST /api/v1/auth/driver/upload-document` (multipart form-data).
- **Connexion OTP** :
  1. `POST /api/v1/auth/login` avec `{"phone_number": "+237699112233"}`
  2. `POST /api/v1/auth/verify-otp` avec `{"phone_number": "+237699112233", "otp_code": "1234"}` $\rightarrow$ Reçoit le JWT `access_token`.

### C. Repères Locaux Camerounais
- **Autocomplétion & Recherche** : `GET /api/v1/poi/search?q=EMIA&city=Yaoundé`
- **Repère le plus proche (Reverse Geocoding)** : `GET /api/v1/poi/nearest?lat=3.8568&lng=11.5015` $\rightarrow$ Renvoie `"Au niveau de Carrefour EMIA"`.

### D. Réservation & Cycle de Vie de la Course
- **Estimation de prix** : `POST /api/v1/rides/estimate`
- **Réserver** : `POST /api/v1/rides`
  - Si `payment_mode: "MOMO"` : Séquestre activé automatiquement. Le passager reçoit `secret_pin` (ex: `"4812"`).
  - Si `payment_mode: "CASH"` : Espèces sélectionnées.
- **Chauffeur Accepte** : `POST /api/v1/rides/{id}/accept`
- **Chauffeur Démarre (Verrouillage)** : `POST /api/v1/rides/{id}/start` $\rightarrow$ Le passager voit disparaître le bouton d'annulation (`is_locked: true`).
- **Validation Arrivée MoMo** : `POST /api/v1/rides/{id}/complete-with-pin` avec `{"pin": "4812"}` dicté par le passager $\rightarrow$ Libère les fonds vers le MoMo du chauffeur.
- **Validation Arrivée Cash** : `POST /api/v1/rides/{id}/complete-cash` $\rightarrow$ Clôture le trajet et déduit la commission VORA.

### E. Assistant Vocal IA (Pidgin & Français)
- `POST /api/v1/ai/voice-intent` avec `{"text": "Drop me for Carrefour EMIA"}`
- Retourne le repère résolu, le mode de transport, l'estimation de prix et une réponse vocale prête à être énoncée par le Text-to-Speech de Flutter.

### F. Sécurité SOS & Suivi Public
- **Déclencher SOS** : `POST /api/v1/rides/{id}/sos` avec coordonnées GPS.
- **Lien web public famille/proches** : `https://vora.cm/track/{share_token}` ou `GET /api/v1/tracking/{share_token}` (sans mot de passe).

---

## 👥 Données de Démonstration Incluses (Seed Data)
À chaque lancement de l'application, les données suivantes sont automatiquement initialisées :
- **18+ Repères Majeurs** : Carrefour EMIA, Marché Mokolo, Pharmacie du Soleil, Total Melen, Poste Centrale, Carrefour Nlongkak, Rond-point Deido, Carrefour Ndokoti, Akwa Palace, etc.
- **2 Alertes Météo / Voirie** :
  - Inondation temporaire Carrefour Warda (Yaoundé) : majoration +25%.
  - Embouteillage critique & chaussée dégradée Ndokoti (Douala) : majoration +30%.
- **Comptes de Test** :
  - Passager : `+237699112233` (Jean-Marc Atangana, OTP: `1234`)
  - Chauffeur Vérifié : `+237677445566` (Paul Mbida, Taxi Jaune `YDE-1420`, Toyota Carina E, OTP: `1234`)

