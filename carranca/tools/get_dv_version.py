"""
get_dv_version.py — Canoa
Prints the version of the installed `data_validate` pip package: runs the venv's
`canoa-data-validate --version` (the app run_validate.sh calls) and takes `__version__`
from its line "The ... version <version> initialized."

Usage:
    python carranca/tools/get_dv_version.py

Layout expected (same as ProcessData.py):
    <apps_parent>/Canoa/            this repo
    <apps_parent>/data_validate/    the validator; its .venv holds the package

Output: only the version (eg `0.7.65b732`), so it can be used in scripts.
Note: `pip show` reports the package version without the build suffix (eg `0.7.65`).
Note: `--version` is not a real option of canoa-data-validate (argparse exits with 2); the version
comes from the banner the app prints on start-up, before it parses the arguments.
Exit code: 0 ok; 1 version not found; 2 data_validate or its venv command not found;
otherwise the command's own exit code.

`run_validator()` is a standalone version of carranca/private/validate_process/run_validator.py:
no sidekick/AppUser/UserSep (they need the Flask app) and it runs any command list.

Equipe da Canoa -- 2026 + Anthropic Claude
mgd 2026-11-09
"""

# cSpell:ignore canoa

import re
import sys
import asyncio
import platform
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APPS_PARENT = REPO_ROOT.parent
DV_FOLDER = "data_validate"  # ValidateProcessConfig.dv_app.folder
DV_COMMAND = "canoa-data-validate"  # console script of the pip package, see run_validate.sh
FLAG_VERSION = "--version"
VERSION_PATTERN = re.compile(r"\bversion\s+(\S+)\s+initialized", re.IGNORECASE)  # "...version 0.7.65b732 initialized."


def decode_std_text(std_text: bytes | None) -> str:
    """py_helper.decode_std_text, simplified: UTF-8 first, then latin-1."""
    if not std_text:
        return ""
    try:
        return std_text.decode("utf-8")
    except UnicodeDecodeError:
        return std_text.decode("latin-1", errors="replace")


async def run_validator(run_command: list[str]) -> tuple[str, str, int]:
    proc = "[get_dv_version]: "
    stdout = None
    stderr = None
    exit_code = 0
    try:
        process = await asyncio.create_subprocess_exec(*run_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        exit_code = process.returncode or 0
    except Exception as e:
        return "", f"{proc}running {' '.join(run_command)}: {e}", 2

    return decode_std_text(stdout), decode_std_text(stderr), exit_code


def get_venv_command(data_validate_path: Path) -> Path:
    if platform.system() == "Windows":
        scripts = data_validate_path / ".venv" / "Scripts"
        # .cmd: a fake canoa-data-validate for tests, since the real package has no Windows install here
        return next((c for ext in (".exe", ".cmd") if (c := scripts / (DV_COMMAND + ext)).is_file()), scripts / (DV_COMMAND + ".exe"))
    return data_validate_path / ".venv" / "bin" / DV_COMMAND


def main() -> int:
    data_validate_path = APPS_PARENT / DV_FOLDER
    if not data_validate_path.is_dir():
        print(f"[get_dv_version] data_validate folder not found: {data_validate_path}")
        return 2

    if not (venv_command := get_venv_command(data_validate_path)).is_file():
        print(f"[get_dv_version] {DV_COMMAND} not found: {venv_command}")
        return 2

    stdout, stderr, exit_code = asyncio.run(run_validator([str(venv_command), FLAG_VERSION]))

    # exit code is ignored: `--version` is not a real option of canoa-data-validate, argparse rejects it (exit 2),
    # but the app prints its "version <x> initialized" banner before parsing the arguments
    if match := VERSION_PATTERN.search(stdout):
        print(match.group(1))
        return 0

    # command failed (eg broken venv) or its output has no "version <x> initialized" line
    print(f"[get_dv_version] could not get the version from {venv_command} {FLAG_VERSION} (exit code {exit_code}).")
    if message := (stderr.strip() or stdout.strip()):
        print(message)
    return exit_code or 1


if __name__ == "__main__":
    sys.exit(main())

# eof
