# Canoa – Relevant File/Folder Structure


```bash
/home/desenv
│
├── canoa_env_vars.txt         # Environment variables used by Canoa
│                              #   see below
├── canoa/                     # Main production Canoa application
│   ├── rema.sh                # Startup script (launches Canoa, see below)
│   ├── requirements.txt       # Python dependencies
│   ├── run_validate.sh        # Launches the data_validate app
│   ├── README.md
│   │
│   ├── carranca/             # Flask/Jinja application code
│   │
│   ├── user_files/           # User-uploaded files
│   │
│   └── LocalStorage/         # Keys & tokens (to be renamed)
│
├── canoa_stage/              # Paused staging version of Canoa
│
├── data_validate/            # External validation app
│   # Source: https://github.com/AdaptaBrasil/data_validate
│
└── data_tunnel/              # Temporary folder for shared files
                              # used by: Canoa ↔ data_validate
```

# rema.sh
```bash
#!/bin/bash
# Run Canoa
# mgd
# Equipe da Canoa -- 2024
# call from <user>l@CanoaVM:~/desenv/canoa/carranca$../rema.sh
source ../../canoa_env_vars.txt
source ../.venv/bin/activate
export CANOA_APP_MODE="Production" # Stage | Development
export FLASK_RUN_PORT="5001"
flask run

```

# canoa_env_vars.txt
```bash
# Canoa Environment Variables
# Call source ../canoa_env_vars.txt
export CANOA_DEBUG="True"
export CANOA_EMAIL_API_KEY_PW="x"
export CANOA_EMAIL_REPORT_CC="a1@canoa.com,a2@canoa.com"
export CANOA_EMAIL_ORIGINATOR="canoa--adaptabrasil@"
export CANOA_SQLALCHEMY_DATABASE_URI="postgresql://"
export FLASK_APP="main"
export FLASK_DEBUG="True"
export FLASK_RUN_HOST="0.0.0.0"
# 2025-10-21
# CANOA_APP_MODE & FLASK_RUN_PORT
# are defined in each rema.sh
# eof
```