# Chess Pro D4 — Architecture (Flutter + Python)

## Stack

| Couche | Techno | Rôle |
|--------|--------|------|
| UI | Flutter (`frontend/flutter_app`) | Desktop Windows + Web, navigation onglets |
| API | FastAPI (`backend/main.py`) **port 3848** | Parties, Stockfish UCI, sauvegardes, rooms locales |
| Moteur | Stockfish via `src/engine/` | UCI asynchrone (thread worker) |
| Legacy | Pygame (`src/`, `main.py`) | Conservé — `LANCER.bat` |

## Important — port 3848

Les ports **8765** et **3847** sont souvent déjà pris.
Chess Pro D4 utilise **3848** — ouvrir `http://127.0.0.1:3848/` dans le navigateur.

## Lancement

1. **FLUTTER.bat** — démarre le backend 3848 puis Flutter Windows  
   ou **BACKEND.bat** puis `flutter run -d windows`

Health : `GET http://127.0.0.1:3848/health` doit contenir `"app":"Chess Pro D4"`.

## Navigation

Rail : Accueil · Jouer · Local · Analyse · Historique · Sauvegardes · Stats · Paramètres  
Paramètres : catégories verticales (Apparence, IA & Stockfish, À propos…).
