# Windows PowerShell dev bootstrap.
$ErrorActionPreference = "Stop"

python -m venv backend\.venv
& backend\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

New-Item -ItemType Directory -Force -Path data\chroma | Out-Null
python -m backend.scripts.run_pipeline
uvicorn backend.app.main:app --reload
