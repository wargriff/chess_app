# Architecture Chess Pro D4

## Vue d'ensemble

```
chess_app/
├── main.py                 # Point d'entrée mince
├── src/
│   ├── app.py              # Boucle applicative / contrôleur
│   ├── core/               # Règles, plateau, session, horloge
│   ├── engine/             # Stockfish UCI asynchrone
│   ├── ui/                 # Pygame UI (D4)
│   ├── services/           # Assets, audio, settings, saves
│   ├── models/             # Données / version / settings
│   └── utils/              # Paths, logging, helpers
├── assets/                 # Graphismes + sons
├── data/                   # saves, settings, cache, logs (runtime)
├── stockfish/              # Binaire moteur (runtime)
├── tests/
├── scripts/ + tools/       # Build / maintenance
└── config/, core/, rendering/, systems/  # Shims compat
```

## Flux

1. `main.py` ajoute la racine au `sys.path` et appelle `src.app.run()`.
2. `ChessApp` charge settings, bootstrap assets, démarre Stockfish en thread UCI.
3. Les coups UI passent par `GameSession` (python-chess) ; le moteur via `StockfishManager` (queue + worker).
4. Rendu : `ChessRenderer` + `InfoPanel` + sidebar + HUD.

## Stockfish

- Détection : `STOCKFISH_PATH`, `stockfish/`, `engines/`, PATH.
- Si absent : téléchargement SF 17.1 (Windows) ou message d'erreur clair.
- Jamais d'appel UCI bloquant sur le thread UI.
