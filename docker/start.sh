#!/bin/bash
cd /app
python -c "import sys; sys.path.insert(0, '.'); from scripts.init_db import init_database; init_database()"
python backend/app.py
