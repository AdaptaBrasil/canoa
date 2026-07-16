"""
check_claude_seals.py — Canoa
Warns (never blocks) when a file certified in `claude-certificate.txt`
has changed since Claude's review, i.e. its current CRC32 no longer
matches the one recorded at review time.

Usage:
    python carranca/tools/check_claude_seals.py

Wired as a local pre-commit hook (.git/hooks/pre-commit); always exits 0.

Equipe da Canoa -- 2026 + Anthropic Claude
mgd 2026-07-15
"""

import sys
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CERTIFICATE = REPO_ROOT / "carranca" / "claude-certificate.txt"


def _crc32(path: Path) -> str:
    return format(zlib.crc32(path.read_bytes()) & 0xFFFFFFFF, "08x")


def main() -> int:
    if not CERTIFICATE.is_file():
        return 0

    stale: list[str] = []
    for line in CERTIFICATE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        rel_path, review_date, recorded_crc32 = (part.strip() for part in line.split("|"))
        file_path = REPO_ROOT / rel_path
        if not file_path.is_file():
            stale.append(f"{rel_path}: certified {review_date}, file no longer exists")
        elif _crc32(file_path) != recorded_crc32:
            stale.append(f"{rel_path}: certified {review_date}, changed since then")

    if stale:
        print("[check_claude_seals] stale Claude review seal(s) found:")
        for msg in stale:
            print(f"  - {msg}")
        print("  (warning only, commit proceeds - update or remove the seal/certificate entry when convenient)")

    return 0


if __name__ == "__main__":
    sys.exit(main())

# eof
