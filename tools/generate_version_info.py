"""Regenere tools/version_info.txt depuis config/version.py."""

from __future__ import annotations

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from config import version as app_version  # noqa: E402

major, minor, patch = (list(map(int, (app_version.VERSION + ".0.0").split("."))) + [0, 0, 0])[:3]
file_ver = f"{major}, {minor}, {patch}, {app_version.BUILD}"
str_ver = f"{major}.{minor}.{patch}.{app_version.BUILD}"

content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({file_ver}),
    prodvers=({file_ver}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', '{app_version.APP_NAME}'),
          StringStruct('FileDescription', '{app_version.APP_NAME} - Echecs avec Stockfish'),
          StringStruct('FileVersion', '{str_ver}'),
          StringStruct('InternalName', '{app_version.APP_ID}'),
          StringStruct('LegalCopyright', '{app_version.APP_NAME}'),
          StringStruct('OriginalFilename', '{app_version.APP_ID}.exe'),
          StringStruct('ProductName', '{app_version.APP_NAME}'),
          StringStruct('ProductVersion', '{str_ver}'),
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""

target = os.path.join(ROOT, "tools", "version_info.txt")
with open(target, "w", encoding="utf-8", newline="\n") as handle:
    handle.write(content)
print(f"version_info.txt -> {str_ver}")
