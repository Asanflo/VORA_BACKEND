# 🚖 VORA Mobility Backend — API REST & WebSockets (FastAPI + SQLModel + SupaBase)

Backend complet et résilient conçu pour propulser l'application mobile Flutter **VORA** (Mobilité urbaine, Taxis jaunes, Covoiturage, Repères populaires et Sécurité adaptés aux réalités du Cameroun).

---

## 📖 Sommaire

1. [Présentation du Projet](#-1-présentation-du-projet)
2. [Dépendances & Procédure d'Installation sur un Autre Ordinateur](#-2-dépendances--procédure-dinstallation-sur-un-autre-ordinateur)
3. [Arborescence Détaillée des Fichiers du Projet](#-3-arborescence-détaillée-des-fichiers-du-projet)
4. [Dictionnaire des Modèles de Données (Tables SQLModel)](#-4-dictionnaire-des-modèles-de-données-tables-sqlmodel)
   - [Modèle User (`users`)](#1-modèle-user-users)
   - [Modèle DriverProfile (`driver_profiles`)](#2-modèle-driverprofile-driver_profiles)
   - [Modèle POI (`pois`)](#3-modèle-poi-pois)
   - [Modèle Ride (`rides`)](#4-modèle-ride-rides)
   - [Modèle EscrowTransaction (`escrow_transactions`)](#5-modèle-escrowtransaction-escrow_transactions)
   - [Modèle NegotiationOffer (`negotiation_offers`)](#6-modèle-negotiationoffer-negotiation_offers)
   - [Modèle WeatherAlert (`weather_alerts`)](#7-modèle-weatheralert-weather_alerts)
5. [Documentation des Endpoints d'API Classés par Fonctionnalité](#-5-documentation-des-endpoints-dapi-classés-par-fonctionnalité)
   - [1. Authentification & Gestion des Comptes](#1-authentification--gestion-des-comptes)
   - [2. Repères Locaux & Géolocalisation (POI)](#2-repères-locaux--géolocalisation-poi)
   - [3. Gestion des Courses & Cycle de Vie](#3-gestion-des-courses--cycle-de-vie)
   - [4. Système de Négociation & Tarif Flexible](#4-système-de-négociation--tarif-flexible)
   - [5. Séquestre Mobile Money & Agrégateur](#5-séquestre-mobile-money--agrégateur)
   - [6. Sécurité & Mode SOS d'Urgence](#6-sécurité--mode-sos-durgence)
   - [7. Suivi Public en Direct (Lien Web Partageable)](#7-suivi-public-en-direct-lien-web-partageable)
   - [8. Assistant Vocal IA (Pidgin & Camfranglais)](#8-assistant-vocal-ia-pidgin--camfranglais)
   - [9. Alertes Météo & État de la Route](#9-alertes-météo--état-de-la-route)
   - [10. Chauffeurs Vérifiés, Badges & Taxis Jaunes](#10-chauffeurs-vérifiés-badges--taxis-jaunes)
   - [11. Canaux WebSockets Temps Réel & Santé](#11-canaux-websockets-temps-réel--santé)
6. [Scénarios de Paiement & Règles d'Arrêt Strictes](#-6-scénarios-de-paiement--règles-darrêt-strictes)

---

## 🌍 1. Présentation du Projet

Au Cameroun (Yaoundé, Douala, etc.), la mobilité urbaine quotidienne repose sur les **taxis jaunes**, mais fait face à des blocages structurels majeurs :
- **L'absence d'adressage précis** : Les usagers n'utilisent pas de numéros de rue, mais des carrefours et des repères populaires (*Carrefour EMIA, Marché Mokolo, Pharmacie du Soleil, Rond-point Deido, Ndokoti*).
- **La méfiance financière** : Risque d'escroquerie pour le client et de non-paiement pour le chauffeur.
- **La cherté des courses privées (dépôts)** : Une course personnelle coûte 2 000 à 5 000 FCFA, alors que le partage de taxi (ramassage) est la norme locale.
- **La rigidité des applications VTC classiques** : L'imposition d'un prix fixe est contraire aux habitudes locales où le prix se négocie selon la pluie, l'état de la chaussée ou l'heure.
- **L'insécurité nocturne** : Risque lié aux faux taxis clandestins.

**VORA** résout ces défis grâce à une architecture logicielle moderne :
1. Moteur de recherche et géocodage par **repères populaires camerounais**.
2. **Paiement séquestre (Escrow)** via Mobile Money (MTN MoMo / Orange Money) avec libération conditionnée à la saisie d'un **Code PIN Oral** dicté par le passager à destination.
3. **Covoiturage urbain** automatique en taxi jaune (groupement par corridor avec -35% de réduction).
4. **Négociation tarifaire bidirectionnelle** en temps réel via WebSockets.
5. **Mode SOS** et lien web de suivi public direct sans mot de passe pour rassurer les proches.
6. **Assistant vocal IA** propulsé par Google Gemini, capable de décoder le **Pidgin** (*"Drop me for Carrefour EMIA"*) et le **Camfranglais** (*"Tu me drop à la Pharmacie du Soleil"*).
7. **Alertes météo et voirie** avec majoration incitative lors des inondations et intempéries.
8. **Profils de confiance** avec badge *Chauffeur Vérifié* et affichage obligatoire du **Numéro de portière de Taxi Jaune** (*ex: YDE-1420*).

---

## 📦 2. Dépendances & Procédure d'Installation sur un Autre Ordinateur

### A. Prérequis Système
- **Python** : Version `3.11`, `3.12`, `3.13` ou `3.14` installée sur la machine.
- **Git** pour le clonage du dépôt.

### B. Principales Dépendances Logicielle (`requirements.txt`)
- **FastAPI** (`>=0.115.0`) : Framework web asynchrone ultra-rapide.
- **Uvicorn** (`>=0.30.0`) : Serveur ASGI haute performance.
- **SQLModel** (`>=0.0.22`) : Créé par Tiangolo, combine SQLAlchemy 2.0 et Pydantic v2 pour unifier tables SQL et schémas d'API.
- **Asyncpg** & **psycopg2-binary** : Drivers PostgreSQL haute vitesse pour SupaBase.
- **Aiosqlite** (`>=0.20.0`) : Driver SQLite asynchrone (permet d'exécuter l'application et les tests instantanément sans serveur externe).
- **Pydantic-Settings** (`>=2.4.0`) : Gestion de la configuration d'environnement (.env).
- **PyJWT[crypto]** & **Bcrypt** : Chiffrement, hachage et tokens d'authentification.
- **Python-Multipart** : Gestion des téléversements de fichiers (pièces CNI, Permis, Carte Grise).
- **HTTPX** : Client HTTP asynchrone pour l'agrégateur de paiement et l'API Gemini.
- **Pytest** & **Pytest-Asyncio** : Suite de tests asynchrones automatisés.

### C. Procédure Pas-à-Pas d'Installation

```bash
# 1. Cloner le projet ou copier le dossier
git clone <URL_DU_DEPOT> Vora_Backend
cd Vora_Backend

# 2. Créer l'environnement virtuel Python
python3 -m venv venv

# 3. Activer l'environnement virtuel
# Sur Linux / macOS :
source venv/bin/activate
# Sur Windows (PowerShell) :
# .\venv\Scripts\Activate.ps1

# 4. Mettre à jour pip et installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configurer les variables d'environnement
cp .env.example .env
```

### D. Configuration de la Base de Données (`.env`)

Ouvrez le fichier `.env` :
- **Option 1 : Démarrage local immédiat (Zéro configuration requise)** :
  Laissez la valeur par défaut `DATABASE_URL="sqlite+aiosqlite:///./vora.db"`. Le fichier SQLite sera créé automatiquement avec toutes les tables et données de démonstration.
- **Option 2 : Connexion SupaBase (PostgreSQL Cloud)** :
  Renseignez la chaîne de connexion SupaBase Pooler ou Direct en préfixant par `postgresql+asyncpg://` :
  ```env
  DATABASE_URL="postgresql+asyncpg://postgres:[VOTRE_MOT_DE_PASSE]@db.[VOTRE_REF_PROJET].supabase.co:5432/postgres"
  SUPABASE_URL="https://[VOTRE_REF_PROJET].supabase.co"
  SUPABASE_KEY="[VOTRE_CLE_SERVICE_OU_ANON]"
  ```

### E. Lancer le Serveur Backend
```bash
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Le serveur démarre immédiatement et initialise automatiquement les tables et les 18+ repères camerounais (`seed_data`).

### F. Exécuter les Tests Automatisés
```bash
PYTHONPATH=. ./venv/bin/pytest -v
```
*Résultat attendu : 11 tests validés à 100% sans avertissement.*

---

## 🗂️ 3. Arborescence Détaillée des Fichiers du Projet

```
Vora_Backend/
├── app/
│   ├── __init__.py                    # Définition du package et version de l'application
│   ├── main.py                        # Point d'entrée FastAPI, cycle de vie (lifespan), CORS, WebSockets
│   ├── api/
│   │   ├── deps.py                    # Dépendances de sécurité (extraction token JWT, rôles Passager/Chauffeur)
│   │   ├── v1/
│   │   │   ├── router.py              # Routeur central V1 agrégeant tous les sous-modules
│   │   │   └── endpoints/
│   │   │       ├── auth.py            # Inscription Passager/Chauffeur, upload des pièces, connexion OTP
│   │   │       ├── poi.py             # Moteur de recherche et reverse geocoding de repères camerounais
│   │   │       ├── rides.py           # Cycle de vie, séquestre MoMo, verrouillage de course, validation PIN/Cash
│   │   │       ├── negotiation.py     # Offres et contre-propositions tarifaires en temps réel
│   │   │       ├── escrow.py          # Consultation du séquestre bancaire et webhooks agrégateurs
│   │   │       ├── sos.py             # Déclenchement alerte SOS d'urgence et simulation SMS
│   │   │       ├── tracking.py        # Suivi public web en direct (sans mot de passe, par share_token)
│   │   │       ├── ai_assistant.py    # Assistant vocal IA (analyse requêtes textuelles et audio)
│   │   │       ├── weather_alerts.py  # Badges zones inondées, pluies battantes et nids-de-poule
│   │   │       └── drivers.py         # Fiche profil de confiance, badges vérifiés et coordonnées GPS
│   │   └── websocket/
│   │       └── connection_manager.py  # Gestionnaire de connexions WebSockets (canaux dédiés et broadcast)
│   ├── core/
│   │   ├── config.py                  # Pydantic Settings (variables d'environnement, secrets, CORS)
│   │   ├── database.py                # Moteur SQLModel Async (gestion pool Supabase Postgres & SQLite)
│   │   ├── security.py                # Fonctions cryptographiques : JWT, normalisation +237, PIN oral, utc_now
│   │   └── seed_data.py               # 18+ repères Yaoundé/Douala, alertes météo et comptes démo injectés au boot
│   ├── models/                        # Modèles SQLModel (Tables PostgreSQL/SQLite + Schémas Pydantic)
│   │   ├── __init__.py                # Exportation globale des modèles
│   │   ├── user.py                    # Tables 'users' et 'driver_profiles' (pièces CNI/Permis, portière taxi)
│   │   ├── poi.py                     # Table 'pois' (repères populaires, alias, popularité)
│   │   ├── ride.py                    # Table 'rides' (statuts, code PIN, token suivi, verrouillage is_locked)
│   │   ├── escrow.py                  # Table 'escrow_transactions' (gel, libération, remboursement MoMo)
│   │   ├── negotiation.py             # Table 'negotiation_offers' (propositions tarifaires des chauffeurs)
│   │   └── weather.py                 # Table 'weather_alerts' (zones à risque et multiplicateurs de prix)
│   ├── schemas/                       # Schémas DTO pour validation stricte des requêtes/réponses Flutter
│   │   ├── auth.py                    # Requêtes/réponses inscription et jetons JWT
│   │   ├── poi.py                     # Schémas recherche et géocodage inverse
│   │   ├── ride.py                    # Schémas estimation, création, détails de course
│   │   ├── escrow.py                  # Schémas séquestre financier
│   │   ├── negotiation.py             # Schémas offres chauffeurs
│   │   ├── sos.py                     # Schémas alerte détresse et suivi live
│   │   ├── ai.py                      # Schémas analyse d'intention vocale
│   │   └── weather.py                 # Schémas alertes météo et voirie
│   └── services/                      # Couche métier pure (isolée des contrôleurs HTTP)
│       ├── aggregator_service.py      # Client séquestre Mobile Money (Hold, Release PIN, Refund, Cash)
│       ├── poi_service.py             # Algorithmes de recherche par mots-clés, alias et distance Haversine
│       ├── pricing_service.py         # Calcul du tarif conseillé, surtaxe pluie et réduction covoiturage
│       ├── shared_ride_service.py     # Algorithme d'appariement de passagers sur corridors similaires
│       ├── negotiation_service.py     # Gestion des offres tarifaires concurrentes
│       ├── sos_service.py             # Traitement des urgences et simulation d'envoi SMS de secours
│       ├── weather_service.py         # Détection des alertes impactant l'itinéraire
│       └── ai_voice_service.py        # Intégration Gemini API + NLU local autonome Pidgin / Camfranglais
├── tests/                             # Suite de tests automatisés pytest
│   ├── conftest.py                    # Fixtures async SQLite en mémoire et client HTTP ASGI
│   ├── test_auth_driver.py            # Test inscription passager/chauffeur avec pièces obligatoires
│   ├── test_poi.py                    # Test recherche repères et repère le plus proche
│   ├── test_escrow_pin_momo.py        # Test complet scénario MoMo : pré-autorisation, PIN oral, libération
│   ├── test_cash_workflow.py          # Test complet scénario Cash : verrouillage démarrage, clôture simple
│   ├── test_negotiation.py            # Test propositions tarifaires et acceptation
│   ├── test_shared_rides.py           # Test groupement automatique de 2 passagers en taxi jaune
│   ├── test_sos.py                    # Test mode SOS et lien public web de suivi
│   ├── test_ai_voice.py               # Test assistant vocal Pidgin et Camfranglais
│   └── test_weather.py                # Test majorations météo sur axes inondés
├── uploads/                           # Dossier local de stockage des pièces justificatives (CNI, Permis)
├── requirements.txt                   # Dépendances Python
├── .env.example                       # Exemple documenté des variables d'environnement
├── .env                              # Fichier d'environnement actif
└── README.md                          # Documentation exhaustive du backend
```

---

## 🗄️ 4. Dictionnaire des Modèles de Données (Tables SQLModel)

### 1. Modèle User (`users`)
Gère les comptes utilisateurs (Passagers, Chauffeurs et Administrateurs).

| Attribut | Type | Contraintes & Valeur par défaut | Description |
|---|---|---|---|
| `id` | `Optional[int]` | Clé Primaire, Autoincrément | Identifiant unique |
| `phone_number` | `str` | Indexé, Unique, Non null | Numéro normalisé au format camerounais (`+2376XXXXXXXX`) |
| `full_name` | `str` | Non null | Nom et prénom de l'utilisateur |
| `role` | `UserRole` (Enum) | Défaut: `UserRole.PASSENGER` | Rôle : `PASSENGER`, `DRIVER`, `ADMIN` |
| `is_active` | `bool` | Défaut: `True` | Compte actif ou désactivé |
| `created_at` | `datetime` | Défaut: `utc_now()` | Horodatage de création du compte |
| *Relation* `driver_profile` | `Optional[DriverProfile]` | Relation 1-to-1 | Profil chauffeur lié si `role == DRIVER` |

---

### 2. Modèle DriverProfile (`driver_profiles`)
Contient les informations d'homologation du taxi jaune, les pièces justificatives et les indicateurs de confiance.

| Attribut | Type | Contraintes & Valeur par défaut | Description |
|---|---|---|---|
| `id` | `Optional[int]` | Clé Primaire, Autoincrément | Identifiant unique du profil |
| `user_id` | `int` | Clé Étrangère (`users.id`), Unique, Indexé | Référence vers le compte utilisateur |
| `cni_number` | `str` | Non null | Numéro officiel de la Carte Nationale d'Identité |
| `cni_document_url` | `Optional[str]` | Nullable | URL/Chemin du document ou photo de la CNI |
| `driver_license_number` | `str` | Non null | Numéro officiel du Permis de Conduire |
| `driver_license_document_url` | `Optional[str]` | Nullable | URL/Chemin de la photo du Permis |
| `vehicle_registration_doc_url` | `Optional[str]` | Nullable | URL/Chemin de la Carte Grise / Attestation |
| `taxi_door_number` | `str` | Indexé, Non null (ex: `YDE-1420`) | **Numéro communal de portière Taxi Jaune** |
| `vehicle_plate` | `str` | Indexé, Non null (ex: `CE 345 BB`) | Plaque d'immatriculation officielle |
| `car_model_color` | `str` | Défaut: `Toyota Corolla Jaune` | Marque, modèle et couleur du véhicule |
| `verification_status` | `VerificationStatus` | Défaut: `PENDING_VERIFICATION` | Statut : `PENDING_VERIFICATION`, `VERIFIED`, `REJECTED` |
| `badges_json` | `str` | Défaut: `'["NOUVEAU_CHAUFFEUR"]'` | Badges de confiance sérialisés en JSON |
| `rating_avg` | `float` | Défaut: `5.0` | Moyenne des avis passagers (sur 5 étoiles) |
| `rides_completed_count` | `int` | Défaut: `0` | Nombre total de courses clôturées |
| `wallet_balance` | `float` | Défaut: `0.0` | Solde du portefeuille chauffeur (prélèvement commission VORA) |
| `current_latitude` | `Optional[float]` | Nullable | Dernière latitude GPS émise par le chauffeur |
| `current_longitude` | `Optional[float]` | Nullable | Dernière longitude GPS émise par le chauffeur |
| `is_available` | `bool` | Défaut: `True` | Disponibilité pour prendre des courses |
| `created_at` | `datetime` | Défaut: `utc_now()` | Date de création du profil |

---

### 3. Modèle POI (`pois`)
Répertoire des repères locaux camerounais utilisés pour la recherche et le géocodage.

| Attribut | Type | Contraintes & Valeur par défaut | Description |
|---|---|---|---|
| `id` | `Optional[int]` | Clé Primaire, Autoincrément | Identifiant unique du repère |
| `name` | `str` | Indexé, Non null | Nom populaire officiel (ex: *Carrefour EMIA*) |
| `city` | `str` | Indexé, Défaut: `Yaoundé` | Ville (*Yaoundé, Douala, etc.*) |
| `category` | `str` | Indexé, Défaut: `Carrefour` | Catégorie (*Carrefour, Marché, Pharmacie, etc.*) |
| `latitude` | `float` | Non null | Latitude GPS exacte |
| `longitude` | `float` | Non null | Longitude GPS exacte |
| `aliases_json` | `str` | Défaut: `'[]'` | Alias, acronymes et noms populaires en JSON |
| `popularity_score` | `int` | Défaut: `10` | Poids de popularité pour le classement de l'autocomplétion |
| `description` | `Optional[str]` | Nullable | Repère visuel immédiat |
| `created_at` | `datetime` | Défaut: `utc_now()` | Horodatage d'ajout |

---

### 4. Modèle Ride (`rides`)
Gère l'intégralité du cycle de vie de la course, le verrouillage de sécurité et la validation.

| Attribut | Type | Contraintes & Valeur par défaut | Description |
|---|---|---|---|
| `id` | `Optional[int]` | Clé Primaire, Autoincrément | Identifiant unique de la course |
| `passenger_id` | `int` | Clé Étrangère (`users.id`), Indexé | Passager ayant commandé la course |
| `driver_id` | `Optional[int]` | Clé Étrangère (`users.id`), Indexé, Nullable | Chauffeur ayant accepté la course |
| `pickup_name` | `str` | Non null | Nom du repère de prise en charge (*ex: Total Melen*) |
| `dropoff_name` | `str` | Non null | Nom du repère de destination (*ex: Poste Centrale*) |
| `pickup_lat` | `float` | Non null | Latitude du point de départ |
| `pickup_lng` | `float` | Non null | Longitude du point de départ |
| `dropoff_lat` | `float` | Non null | Latitude du point d'arrivée |
| `dropoff_lng` | `float` | Non null | Longitude du point d'arrivée |
| `pickup_poi_id` | `Optional[int]` | Clé Étrangère (`pois.id`), Nullable | ID du repère POI de départ si associé |
| `dropoff_poi_id` | `Optional[int]` | Clé Étrangère (`pois.id`), Nullable | ID du repère POI d'arrivée si associé |
| `payment_mode` | `PaymentMode` | Défaut: `PaymentMode.MOMO` | Mode : `MOMO` (Séquestre) ou `CASH` (Espèces) |
| `ride_type` | `RideType` | Défaut: `RideType.SOLO` | Type : `SOLO` (Course exclusive) ou `SHARED` (Covoiturage) |
| `suggested_price` | `float` | Non null | Prix conseillé calculé par le système en FCFA |
| `agreed_price` | `float` | Non null | Prix final convenu après négociation en FCFA |
| `status` | `RideStatus` | Indexé, Défaut: `REQUESTED` | Statut : `REQUESTED`, `NEGOTIATING`, `ACCEPTED`, `STARTED`, `COMPLETED`, `CANCELLED` |
| `is_locked` | `bool` | Défaut: `False` | **Verrouillage absolu** : devient `True` au démarrage, annulation bloquée |
| `secret_pin` | `str` | Non null (ex: `4821`) | **Code PIN Oral** à 4 chiffres généré (visible uniquement par le passager) |
| `pin_attempts` | `int` | Défaut: `0` | Compteur de tentatives de saisie PIN par le chauffeur (max 3) |
| `share_token` | `str` | Unique, Indexé, Token URL-Safe | Jeton public pour le lien de suivi web en direct |
| `is_sos_active` | `bool` | Défaut: `False` | Indicateur d'alerte SOS déclenchée |
| `sos_activated_at` | `Optional[datetime]` | Nullable | Horodatage du déclenchement SOS |
| `shared_group_id` | `Optional[str]` | Indexé, Nullable | Identifiant de groupe pour les courses partagées |
| `commission_amount` | `float` | Défaut: `0.0` | Commission VORA calculée en FCFA |
| `created_at` | `datetime` | Défaut: `utc_now()` | Horodatage de réservation |
| `started_at` | `Optional[datetime]` | Nullable | Horodatage de démarrage effectif |
| `completed_at` | `Optional[datetime]` | Nullable | Horodatage de fin de course |
| `cancelled_at` | `Optional[datetime]` | Nullable | Horodatage d'annulation (si avant démarrage) |

---

### 5. Modèle EscrowTransaction (`escrow_transactions`)
Journalise les transactions de séquestre Mobile Money gérées par l'agrégateur.

| Attribut | Type | Contraintes & Valeur par défaut | Description |
|---|---|---|---|
| `id` | `Optional[int]` | Clé Primaire, Autoincrément | Identifiant unique de transaction |
| `ride_id` | `int` | Clé Étrangère (`rides.id`), Unique, Indexé | Course associée |
| `passenger_phone` | `str` | Non null | Numéro MoMo débité pour le séquestre |
| `driver_phone` | `Optional[str]` | Nullable | Numéro MoMo crédité à la validation du PIN |
| `amount` | `float` | Non null | Montant total gelé en FCFA |
| `commission_amount` | `float` | Défaut: `0.0` | Commission prélevée par la plateforme VORA |
| `driver_net_amount` | `float` | Défaut: `0.0` | Montant net versé au chauffeur |
| `provider` | `PaymentProvider` | Défaut: `MTN_MOMO` | Fournisseur : `MTN_MOMO`, `ORANGE_MONEY`, `CASH` |
| `aggregator_reference` | `Optional[str]` | Nullable | Référence de transaction externe de l'agrégateur |
| `status` | `EscrowStatus` | Défaut: `PENDING_HOLD` | Statut : `PENDING_HOLD`, `HELD`, `RELEASED`, `REFUNDED` |
| `held_at` | `Optional[datetime]` | Nullable | Date et heure de pré-autorisation et gel |
| `released_at` | `Optional[datetime]` | Nullable | Date et heure de libération vers le chauffeur |
| `refunded_at` | `Optional[datetime]` | Nullable | Date et heure de remboursement au passager |
| `created_at` | `datetime` | Défaut: `utc_now()` | Horodatage de création |

---

### 6. Modèle NegotiationOffer (`negotiation_offers`)
Stocke les offres de prix et contre-propositions soumises par les chauffeurs.

| Attribut | Type | Contraintes & Valeur par défaut | Description |
|---|---|---|---|
| `id` | `Optional[int]` | Clé Primaire, Autoincrément | Identifiant unique de l'offre |
| `ride_id` | `int` | Clé Étrangère (`rides.id`), Indexé | Course ciblée |
| `driver_id` | `int` | Clé Étrangère (`users.id`), Indexé | Chauffeur proposant l'offre |
| `offered_price` | `float` | Non null | Prix proposé par le chauffeur en FCFA |
| `driver_eta_minutes` | `int` | Défaut: `5` | Temps d'approche estimé en minutes |
| `status` | `OfferStatus` | Défaut: `PENDING` | Statut : `PENDING`, `ACCEPTED`, `REJECTED`, `EXPIRED` |
| `created_at` | `datetime` | Défaut: `utc_now()` | Horodatage de soumission |

---

### 7. Modèle WeatherAlert (`weather_alerts`)
Cartographie les zones sinistrées, inondations et nids-de-poule pour ajustement tarifaire dynamique.

| Attribut | Type | Contraintes & Valeur par défaut | Description |
|---|---|---|---|
| `id` | `Optional[int]` | Clé Primaire, Autoincrément | Identifiant unique de l'alerte |
| `title` | `str` | Non null | Titre de l'alerte (*ex: Axe Submergé Carrefour Warda*) |
| `alert_type` | `WeatherAlertType` | Défaut: `HEAVY_RAIN` | Type : `HEAVY_RAIN`, `FLOODING`, `ROAD_DAMAGE`, `TRAFFIC_JAM` |
| `severity` | `AlertSeverity` | Défaut: `WARNING` | Niveau : `INFO`, `WARNING`, `DANGER` |
| `city` | `str` | Indexé, Défaut: `Yaoundé` | Ville concernée |
| `latitude` | `float` | Non null | Latitude GPS du centre de l'aléa |
| `longitude` | `float` | Non null | Longitude GPS du centre de l'aléa |
| `radius_meters` | `float` | Défaut: `800.0` | Rayon d'impact en mètres |
| `fare_multiplier` | `float` | Défaut: `1.20` | Facteur de majoration tarifaire (ex: 1.25 = +25%) |
| `eta_penalty_minutes` | `int` | Défaut: `10` | Délai de circulation additionnel estimé |
| `is_active` | `bool` | Indexé, Défaut: `True` | Alerte active ou levée |
| `description` | `Optional[str]` | Nullable | Détails ou consignes de circulation |
| `created_at` | `datetime` | Défaut: `utc_now()` | Date d'enregistrement |

---

## 📡 5. Documentation des Endpoints d'API Classés par Fonctionnalité

Toutes les routes de l'API sont préfixées par `/api/v1`.

### 1. Authentification & Gestion des Comptes
Gestion des inscriptions, connexion par code OTP sur téléphone camerounais (+237) et transmission des pièces justificatives chauffeur.

| Méthode | Route | Description | Corps de Requête / Paramètres | Réponse & Codes HTTP |
|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Demande d'OTP par SMS | `{"phone_number": "+237699112233"}` | `200 OK` (Message d'envoi OTP) |
| `POST` | `/api/v1/auth/verify-otp` | Validation OTP & émission du JWT | `{"phone_number": "+237699112233", "otp_code": "1234"}` | `200 OK` (Jeton `access_token` + Profil) |
| `POST` | `/api/v1/auth/passenger/register` | Inscription nouveau passager | `{"phone_number": "+237699112233", "full_name": "Samuel Eto'o"}` | `200 OK` (Jeton + Profil passager) |
| `POST` | `/api/v1/auth/driver/register` | Inscription chauffeur avec pièces | `DriverRegisterRequest` (CNI, Permis, Numéro portière `YDE-1420`, Plaque) | `200 OK` (Jeton + Profil `PENDING_VERIFICATION`) |
| `POST` | `/api/v1/auth/driver/upload-document` | Téléversement d'une pièce | `multipart/form-data` : `document_type` + `file` | `200 OK` (URL publique du document) |
| `GET` | `/api/v1/auth/me` | Profil connecté | Header `Authorization: Bearer <token>` | `200 OK` (Détails utilisateur & chauffeur) |

---

### 2. Repères Locaux & Géolocalisation (POI)
Moteur d'adressage populaire camerounais (résolution de Carrefour EMIA, Marché Mokolo, etc.).

| Méthode | Route | Description | Paramètres de Requête (Query) | Réponse & Codes HTTP |
|---|---|---|---|---|
| `GET` | `/api/v1/poi/search` | Recherche fuzzy par nom/alias | `q=EMIA&city=Yaoundé&limit=10` | `200 OK` (`List[POIRead]`) |
| `GET` | `/api/v1/poi/nearest` | Repère le plus proche (Reverse Geocoding) | `lat=3.8568&lng=11.5015&city=Yaoundé` | `200 OK` (*"Au niveau de Carrefour EMIA"*) |
| `GET` | `/api/v1/poi` | Liste tous les repères | `city=Yaoundé&category=Carrefour` | `200 OK` (`List[POIRead]`) |
| `POST` | `/api/v1/poi` | Ajouter un nouveau repère | `POICreate` (nom, coordonnées, alias, score) | `201 Created` (`POIRead`) |

---

### 3. Gestion des Courses & Cycle de Vie
Création de courses, sélection MoMo (Séquestre) vs Cash, verrouillage au démarrage et validation d'arrivée.

| Méthode | Route | Description | Paramètres / Corps | Réponse & Codes HTTP |
|---|---|---|---|---|
| `POST` | `/api/v1/rides/estimate` | Estimation tarif, distance et impact météo | `RideEstimateRequest` (départ, arrivée, solo/partagé) | `200 OK` (Prix solo/partagé, surtaxe pluie) |
| `POST` | `/api/v1/rides` | Réserver une course (MoMo ou Espèces) | `RideCreateRequest` (départ, destination, mode de paiement) | `201 Created` (`RideRead` avec `secret_pin`) |
| `GET` | `/api/v1/rides/{ride_id}` | Détails d'une course | Header Auth (PIN masqué si non-propriétaire) | `200 OK` (`RideRead`) |
| `POST` | `/api/v1/rides/{ride_id}/accept` | Chauffeur accepte la course | Header Auth Chauffeur | `200 OK` (`RideActionResponse`) |
| `POST` | `/api/v1/rides/{ride_id}/start` | Chauffeur démarre (**Verrouillage absolu**) | Header Auth Chauffeur | `200 OK` (`is_locked = True`, annulation bloquée) |
| `POST` | `/api/v1/rides/{ride_id}/complete-with-pin` | Validation MoMo par Code PIN Oral | `{"pin": "4821"}` (dicté par le passager) | `200 OK` (Fonds libérés vers le chauffeur) |
| `POST` | `/api/v1/rides/{ride_id}/complete-cash` | Validation course Espèces (sans PIN) | Header Auth Chauffeur | `200 OK` (Course terminée, commission prélevée) |
| `POST` | `/api/v1/rides/{ride_id}/cancel` | Annuler la course (bloqué si démarrée) | Header Auth Passager/Chauffeur | `200 OK` (Remboursement si MoMo) ou `400 Bad Request` |

---

### 4. Système de Négociation & Tarif Flexible
Négociation InDrive adaptée à la culture locale des taxis au Cameroun.

| Méthode | Route | Description | Corps de Requête | Réponse & Codes HTTP |
|---|---|---|---|---|
| `POST` | `/api/v1/rides/{ride_id}/negotiation/offer` | Chauffeur soumet une contre-proposition | `{"offered_price": 1800.0, "driver_eta_minutes": 5}` | `200 OK` (Offre émise et broadcastée) |
| `GET` | `/api/v1/rides/{ride_id}/negotiation/offers` | Passager consulte les offres reçues | Header Auth Passager | `200 OK` (`List[NegotiationOfferRead]`) |
| `POST` | `/api/v1/rides/{ride_id}/negotiation/offers/{offer_id}/accept` | Passager accepte l'offre d'un chauffeur | Header Auth Passager | `200 OK` (Tarif figé, chauffeur assigné) |

---

### 5. Séquestre Mobile Money & Agrégateur
Consultation de l'état des fonds gelés et écoute des webhooks d'agrégateurs (Campay, NotchPay, CinetPay).

| Méthode | Route | Description | Paramètres / Corps | Réponse & Codes HTTP |
|---|---|---|---|---|
| `GET` | `/api/v1/escrow/ride/{ride_id}` | État des fonds séquestrés d'une course | Header Auth | `200 OK` (Statut: `HELD`, `RELEASED`, `REFUNDED`) |
| `POST` | `/api/v1/escrow/webhook` | Webhook de retour agrégateur de paiement | JSON de callback avec référence et statut | `200 OK` (`{"received": true}`) |

---

### 6. Sécurité & Mode SOS d'Urgence
Protection des usagers lors des déplacements nocturnes ou à risque.

| Méthode | Route | Description | Corps de Requête | Réponse & Codes HTTP |
|---|---|---|---|---|
| `POST` | `/api/v1/rides/{ride_id}/sos` | Déclencher l'alerte d'urgence SOS | `{"latitude": 3.8568, "longitude": 11.5015, "message": "Urgence"}` | `200 OK` (Position broadcastée & SMS logué) |

---

### 7. Suivi Public en Direct (Lien Web Partageable)
Permet à la famille et aux proches de suivre en temps réel le déplacement sans avoir besoin de compte.

| Méthode | Route | Description | Paramètres | Réponse & Codes HTTP |
|---|---|---|---|---|
| `GET` | `/api/v1/tracking/{share_token}` | Page web publique de suivi en direct | `share_token` (Jeton cryptographique) | `200 OK` (Position taxi, portière, chauffeur, état SOS) |

---

### 8. Assistant Vocal IA (Pidgin & Camfranglais)
Compréhension du langage parlé pour passagers et chauffeurs en situation de mobilité.

| Méthode | Route | Description | Paramètres / Corps | Réponse & Codes HTTP |
|---|---|---|---|---|
| `POST` | `/api/v1/ai/voice-intent` | Extraction d'intention depuis du texte dicté | `{"text": "Drop me for Carrefour EMIA"}` | `200 OK` (Repères résolus, tarif, réponse vocale) |
| `POST` | `/api/v1/ai/voice-audio` | Téléversement d'un enregistrement audio micro | `multipart/form-data` : fichier audio | `200 OK` (Transcription et intention extraite) |

---

### 9. Alertes Météo & État de la Route
Visualisation des aléas climatiques (fortes pluies, inondations, nids-de-poule) pour les badges de carte Flutter.

| Méthode | Route | Description | Paramètres / Corps | Réponse & Codes HTTP |
|---|---|---|---|---|
| `GET` | `/api/v1/weather-alerts/active` | Liste des zones sinistrées actives | `city=Yaoundé` | `200 OK` (Badges, coordonnées, majoration prix) |
| `POST` | `/api/v1/weather-alerts` | Signaler une nouvelle alerte de voirie | `WeatherAlertCreate` (titre, coordonnées, rayon, surtaxe) | `201 Created` (`WeatherAlertRead`) |

---

### 10. Chauffeurs Vérifiés, Badges & Taxis Jaunes
Vérification des chauffeurs, gestion du numéro de portière communal et transmission GPS en direct.

| Méthode | Route | Description | Paramètres / Corps | Réponse & Codes HTTP |
|---|---|---|---|---|
| `GET` | `/api/v1/drivers/{driver_id}/profile` | Fiche de confiance publique chauffeur | ID du chauffeur | `200 OK` (Numéro de portière, plaque, badges, note) |
| `POST` | `/api/v1/drivers/location` | Chauffeur met à jour sa position GPS | `{"latitude": 3.8568, "longitude": 11.5015}` | `200 OK` (Position diffusée en temps réel) |
| `POST` | `/api/v1/drivers/{driver_id}/verify` | Validation administrative des pièces | ID du chauffeur | `200 OK` (Statut `VERIFIED` + attribution des badges) |

---

### 11. Canaux WebSockets Temps Réel & Santé

| Protocole | Route | Description | Données Échangées |
|---|---|---|---|
| `WS` | `/ws/rides/{ride_id}` | Canal temps réel dédié à une course | Événements : `ride:accepted`, `ride:started`, `negotiation:offer_received`, `sos:alert`, `ride:completed` |
| `WS` | `/ws/global` | Canal de diffusion globale chauffeurs | Événements : `ride:requested`, `driver:location_updated` |
| `GET` | `/health` | Diagnostic de santé de l'API | `200 OK` (`{"status": "healthy", "version": "1.0.0"}`) |
| `GET` | `/` | Racine de bienvenue avec liens doc | `200 OK` (Liens vers `/docs` et `/redoc`) |

---

## 🔒 6. Scénarios de Paiement & Règles d'Arrêt Strictes

```
                      [ Passager réserve la course ]
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
 🔄 MODE MOBILE MONEY (Séquestre)                   💵 MODE ESPÈCES (Cash)
           │                                                   │
  [ 1. Pré-autorisation & Blocage ]                            │
  (Fonds gelés sur séquestre agrégateur)                       │
           │                                                   │
           ├─────────────────────────┬─────────────────────────┤
           ▼                         ▼                         ▼
   [ Chauffeur Accepte ]     [ Chauffeur Accepte ]             │
           │                         │                         │
           ▼                         ▼                         ▼
   [ Chauffeur clique        [ Chauffeur clique                │
   "Démarrer la course" ]    "Démarrer la course" ]            │
           │                         │                         │
   ↳ VERROUILLAGE TOTAL      ↳ VERROUILLAGE TOTAL              │
   (Annulation désactivée)   (Annulation désactivée)           │
           │                         │                         │
           ▼                         ▼                         ▼
   [ Arrivée à Destination ] [ Arrivée à Destination ]         │
           │                         │                         │
   ↳ Passager dicte son      ↳ Passager remet les billets      │
     Code PIN Oral (4 chiffres) en main propre                 │
           │                         │                         │
           ▼                         ▼                         ▼
   [ Chauffeur saisit        [ Chauffeur clique                │
     le Code PIN ]             "Valider / Terminer" ]          │
           │                         │                         │
   ↳ Déclencheur :           ↳ Déclencheur :                   │
     Vérification PIN ->       Validation directe ->           │
     Libération instantanée    Clôture course &                │
     du séquestre vers MoMo    déduction commission VORA       │
     du chauffeur.             sur solde chauffeur.            │
```

| Critère | Mode Mobile Money (MoMo) | Mode Espèces (Cash) |
|---|---|---|
| **Séquestre / Blocage Bancaire** | **Oui** (Fonds pré-autorisés et gelés à la commande) | **Non** (Paiement physique à l'arrivée) |
| **Au Démarrage Chauffeur** | **Verrouillage absolu** (Annulation passager bloquée) | **Verrouillage absolu** (Annulation passager bloquée) |
| **Validation d'Arrivée** | Saisie obligatoire du **Code PIN Oral** du passager | Simple clic sur *"Valider / Terminer la course"* |
| **Déclencheur Final** | La validation du PIN libère les fonds vers le chauffeur | La validation clôture la course et prélève la commission |

---

## 🏆 Données de Démonstration Pré-injectées (Seed Data)

À chaque démarrage, la base de données s'auto-initialise avec :
- **18+ Repères Majeurs** : *Carrefour EMIA, Marché Mokolo, Pharmacie du Soleil, Total Melen, Poste Centrale, Carrefour Nlongkak, Carrefour Warda, Carrefour Bastos, Carrefour Biyem-Assi Express, Carrefour Obili, Carrefour Vogt, Hôpital Général, Rond-Point Deido, Carrefour Ndokoti, Ange Raphaël, Marché Sandaga, Akwa Palace, Place du Gouvernement Bonanjo*.
- **2 Alertes Météo & Voirie Actives** :
  - *Axe Submergé / Warda* (Yaoundé) : majoration tarifaire +25%.
  - *Embouteillage Monstre & Chaussée Glissante / Ndokoti* (Douala) : majoration tarifaire +30%.
- **Comptes de Démonstration Prêts à l'Emploi** :
  - **Passager** : `+237699112233` (Nom: *Jean-Marc Atangana*, Code OTP: `1234`)
  - **Chauffeur Vérifié** : `+237677445566` (Nom: *Paul Mbida*, Taxi Jaune `YDE-1420`, Plaque `CE 789 AA`, Toyota Carina E Jaune, Note: 4.9⭐, Code OTP: `1234`)
