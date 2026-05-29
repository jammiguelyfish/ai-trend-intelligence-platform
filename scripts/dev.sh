#!/usr/bin/env bash
# Convenience helper: full local bootstrap (Linux/macOS).
set -euo pipefail

python -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

mkdir -p data/chroma
python -m backend.scripts.run_pipeline
uvicorn backend.app.main:app --reload
