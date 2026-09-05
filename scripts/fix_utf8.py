# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r"C:\Users\wargriff\Pycharm_Project_v 3.12\chess_app\frontend\flutter_app\lib\screens\extra_screens.dart")
t = p.read_text(encoding="utf-8")
repl = {
    "Ã‰": "É",
    "Ã¨": "è",
    "Ã©": "é",
    "Ã ": "à",
    "Ã§": "ç",
    "Å“": "œ",
    "â€”": "—",
    "â€¦": "…",
    "Ã´": "ô",
    "Â·": "·",
    "copiÃ©": "copié",
    "sauvegardÃ©e": "sauvegardée",
    "DÃ©faites": "Défaites",
}
for a, b in repl.items():
    t = t.replace(a, b)
p.write_text(t, encoding="utf-8")
print("remaining bad:", "Ã" in t or "â€" in t or "Â·" in t)
