# -*- coding: utf-8 -*-
from pathlib import Path
import ast

p = Path(__file__).resolve().parents[1] / "backend" / "main.py"
lines = p.read_text(encoding="utf-8").splitlines(True)
out: list[str] = []
i = 0
marker = 'return HTMLResponse(content=html, media_type="text/html; charset=utf-8")'
while i < len(lines):
    line = lines[i]
    out.append(line)
    if marker in line:
        i += 1
        while i < len(lines) and not lines[i].startswith("async def _broadcast"):
            i += 1
        continue
    i += 1

text = "".join(out)
ast.parse(text)
p.write_text(text, encoding="utf-8")
print(f"fixed: {len(lines)} -> {len(out)} lines")
