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
│   ├── carranca/              # Flask/Jinja application code
│   │
│   ├── exported_data/         # Working folder for exporting schemas
│   │
│   ├── spatial_files/         # Admin uploaded Spatial Data Files
│   │
│   └── user_files/            # User-uploaded files
│
├── canoa_stage/               # Paused staging version of Canoa
│
├── data_validate/             # External validation app
│   # Source: https://github.com/AdaptaBrasil/data_validate
│
├── local-storage/             # Api Keys & tokens
│
│
└── data_tunnel/               # Temporary folder for shared files
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
export FLASK_USE_RELOADER=0
flask run
#eof

```

# canoa_env_vars.txt
```bash
# Canoa Environment Variables
# Call source ../canoa_env_vars.txt
export CANOA_DEBUG="False"   # "True" on a server forces debug on in any mode (red badge)
# export CANOA_DISPLAY_MUTE="True"   # silences the start-up log; omit for the verbose default
export CANOA_EMAIL_PROVIDER="SMTP"
export CANOA_EMAIL_API_KEY_PW="x"
export CANOA_EMAIL_REPORT_CC="a1@domain.com,Name One;a2@domain.com,Name Two"   # email,name;email,name
export CANOA_EMAIL_ORIGINATOR="originator@domain.com"
## NAT Adapter:: export CANOA_SQLALCHEMY_DATABASE_URI="postgresql://user:pw@10.0.0.1:5432/dbname"
## Bridge Adapter (the VM's address on the LAN)
export CANOA_SQLALCHEMY_DATABASE_URI="postgresql://user:pw@<db-host>:5432/dbname"
export FLASK_APP="main"
export FLASK_DEBUG=0
export FLASK_RUN_HOST="0.0.0.0"
# 2025-10-21
# CANOA_APP_MODE & FLASK_RUN_PORT
# are defined in each rema.sh
```
---
<small>_eof_</small>
