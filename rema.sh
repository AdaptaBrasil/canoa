#!/bin/bash
# Run Canoa
# mgd
# Equipe da Canoa -- 2024
# call from miguel@CanoaVM:~/desenv/canoa/carranca$../rema.sh
source ../../canoa_env_vars.txt
source ../.venv/bin/activate
export CANOA_APP_MODE="Production"
export FLASK_RUN_PORT="5001"
flask run
