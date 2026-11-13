#!/bin/bash
# Run Canoa
# mgd
# Equipe da Canoa -- 2024,2025,2026
# call from miguel@CanoaVM:~/desenv/canoa/carranca$ ../rema.sh
# secrets and host values come from canoa_env_vars.txt; every run setting is here, in git
source ../../canoa_env_vars.txt
source ../.venv/bin/activate
export CANOA_APP_MODE="Production"
export CANOA_DEBUG="False"
export FLASK_APP="main"
export FLASK_DEBUG=0
export FLASK_RUN_HOST="0.0.0.0"
export FLASK_RUN_PORT="5001"
export FLASK_RUN_RELOAD=0
flask run
#eof
