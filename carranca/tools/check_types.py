"""
check_types.py — Canoa
Runs Pyright (via `npx`, no local install needed) for static type checking.

Usage:
    python carranca/ai_works/check_types.py [path ...]

With no arguments, checks the UI-texts subsystem (the files reviewed on 2026-07-02):
    carranca/helpers/ui_db_texts_manager.py
    carranca/common/UIDBTexts.py
    carranca/common/UITextsKeys.py

Equipe da Canoa -- 2026 + Anthropic Claude
mgd 2026-07-02
"""

# cSpell:words pyright

import sys
import platform
import subprocess

DEFAULT_TARGETS = [
    "carranca/helpers/ui_db_texts_manager.py",
    "carranca/common/UIDBTexts.py",
    "carranca/common/UITextsKeys.py",
]


def main() -> int:
    targets = sys.argv[1:] or DEFAULT_TARGETS
    cmd = ["npx", "--yes", "pyright", *targets]
    print(f"$ {' '.join(cmd)}")
    # on Windows, npx is a .cmd shim: subprocess needs shell=True to resolve it via PATH
    return subprocess.run(cmd, shell=(platform.system() == "Windows")).returncode


if __name__ == "__main__":
    sys.exit(main())

# eof
