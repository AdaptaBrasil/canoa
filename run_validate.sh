#!/bin/bash
# Translated by Copilot 2024.06.27 from run_validate.bat (mgd)
#   and again in 2024.07.29
#   mgd 2024-07-27 v2 (param1: data_validate folder)
#   mgd 2025-11-24 v3 (call a pip package)
# Equipe da Canoa -- 2024
#
# /!\ Keep synced with run_validate.bat
# ----------------------------------
# Change to the data_validate folder
cd "$1"
shift
echo "Activating data_validate environment in Linux..."
source .venv/bin/activate  # Activate the virtual environment
echo "Running data_validate..."
canoa-data-validate "$@"
echo "Deactivating data_validate environment..."
deactivate
echo "Returning to Canoa."
# eof
