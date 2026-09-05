# Architecture Chess Pro D4

## Vue d'ensemble

```
chess_app/
├── main.py                 # Point d'entrée mince
├── LANCER.bat / BUILD.bat  # Lancement & build Windows
├── src/
│   ├── app.py              # Boucle applicative / contrôleur
│   ├── core/               # Règles, plateau, session, horloge
│   ├── engine/             # Stockfish UCI asynchrone
│   ├── ui/                 # Pygame UI (D4)
│   ├── services/           # Assets, audio, settings, saves JSON
│   ├── models/             # Données / version / settings
│   └── utils/              # Paths, logging, helpers
├── assets/                 # Graphismes + sons
├── saves/                  # Sauvegardes JSON de parties
├── logs/                   # chess_pro.log
├── stockfish/              # Binaire moteur
├── tests/
├── scripts/test_all.py
├── tools/                  # Build / maintenance
└── config/, core/, rendering/, systems/  # Shims compat (outils legacy)
```

## Frontend

Deux interfaces :

1. **Flutter** (recommandé) — `frontend/flutter_app/` + **port API 3848**  
   Lancer via `FLUTTER.bat` (démarre backend + UI). Voir `docs/FLUTTER_STACK.md`.
2. **Pygame** (legacy) — `main.py` / `LANCER.bat` — conservé.

> Note : le port **8765** / **3847** sont souvent déjà pris ; Chess Pro D4 utilise **3848**.

## Flux

1. `main.py` → `src.app.run()`.
2. `ChessApp` charge settings, bootstrap, démarre Stockfish (thread UCI).
3. Coups via `GameSession` (python-chess) ; moteur via `StockfishManager`.
4. Sauvegarde JSON complète (`SaveManager.save_game`) + PGN secondaire.

## UI shell (refonte)

- Header : marque adaptative + statut Stockfish (● en ligne / hors ligne)
- Navigation : Partie | Analyse | Historique | Sauvegardes | Stats | Paramètres
- Actions bas : uniquement Nouvelle partie / Annuler / Refaire (onglet Partie)
- Breakpoints : XS/SM/MD/LG/XL — plateau prioritaire, panneaux conditionnels
- Décorations (particules, ornements, brouillard) : retirées
