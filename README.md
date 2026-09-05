# Chess Pro D4

Jeu d'échecs Windows professionnel (Pygame + Stockfish UCI).

## Lancer

```bat
Lancer.bat
```

ou en développement :

```bat
py -3.12 main.py
```

## Contre Stockfish

1. Menu → **JOUER CONTRE STOCKFISH**
2. Jouez les Blancs (défaut)
3. Après votre coup, le bandeau **Stockfish réfléchit...** apparaît
4. Le coup du moteur s'anime sur l'échiquier

Logs techniques : `data/logs/chesspro.log`

## Compiler l'exe

```bat
py -3.12 tools\build_exe.py
```

Résultat : `dist\ChessPro\ChessPro.exe`

## Tests

```bat
py -3.12 -m pytest tests/ -q
```

## Architecture

Voir [ARCHITECTURE.md](ARCHITECTURE.md).
