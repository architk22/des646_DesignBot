# DDI Checker

Simple Drug–Drug Interaction (DDI) app with a FastAPI backend and a Streamlit frontend.

## Prerequisites
- Windows
- Python 3.10+ (project used Python 3.13)
- Git (optional)

## Install and run

1. From the project root:
```powershell
# create venv and activate (PowerShell)
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

# upgrade packaging tools and install deps
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r .\requirements.txt
```

2. Start the backend (run from project root):
```powershell
# start uvicorn
python -m uvicorn Backend.app:app --reload --host 127.0.0.1 --port 8000
# API docs: http://127.0.0.1:8000/docs
```

3. Start the frontend (new terminal, activate the same venv):
```powershell
# set backend URL (optional)
$env:BACKEND_URL = "http://127.0.0.1:8000"

# run streamlit
streamlit run frontend/app.py --server.port 8501
# Frontend: http://localhost:8501
```

## Common issues & fixes
- "Fatal error in launcher" for pip: use `python -m pip install -r requirements.txt` or recreate the venv.
- `ModuleNotFoundError: No module named 'Backend'`: run uvicorn from the project root or set PYTHONPATH so Python can import the package.
- `ModuleNotFoundError: No module named 'fuzzywuzzy'`: install `fuzzywuzzy` (and optional `python-Levenshtein`) into the venv:
  `python -m pip install fuzzywuzzy python-Levenshtein`
- Activation errors (execution policy): `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## API (key endpoints)
- GET / — health
- GET /autocomplete?query=aspirin — suggestions
- POST /check — body: { "new_drug": "X", "current": ["A","B"], "patient_name": "...", "age": 45 }
- GET /visits — recent checks

## Project layout
- Backend/ — FastAPI app, data, retrieval/normalizer modules
- frontend/ — Streamlit UI (frontend/app.py)
- requirements.txt — Python dependencies

## Notes
- Keep two terminals open when developing (backend + frontend).
- If changing imports to the maintained fork, replace `fuzzywuzzy` with `thefuzz` and update requirements.

```// filepath: c:\Users\pawan\OneDrive\Desktop\des646_DesignBot\README.md
# DDI Checker

Simple Drug–Drug Interaction (DDI) app with a FastAPI backend and a Streamlit frontend.

## Prerequisites
- Windows
- Python 3.10+ (project used Python 3.13)
- Git (optional)

## Install and run

1. From the project root:
```powershell
# create venv and activate (PowerShell)
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

# upgrade packaging tools and install deps
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r .\requirements.txt
```

2. Start the backend (run from project root):
```powershell
# start uvicorn
python -m uvicorn Backend.app:app --reload --host 127.0.0.1 --port 8000
# API docs: http://127.0.0.1:8000/docs
```

3. Start the frontend (new terminal, activate the same venv):
```powershell
# set backend URL (optional)
$env:BACKEND_URL = "http://127.0.0.1:8000"

# run streamlit
streamlit run frontend/app.py --server.port 8501
# Frontend: http://localhost:8501
```

## Common issues & fixes
- "Fatal error in launcher" for pip: use `python -m pip install -r requirements.txt` or recreate the venv.
- `ModuleNotFoundError: No module named 'Backend'`: run uvicorn from the project root or set PYTHONPATH so Python can import the package.
- `ModuleNotFoundError: No module named 'fuzzywuzzy'`: install `fuzzywuzzy` (and optional `python-Levenshtein`) into the venv:
  `python -m pip install fuzzywuzzy python-Levenshtein`
- Activation errors (execution policy): `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## API (key endpoints)
- GET / — health
- GET /autocomplete?query=aspirin — suggestions
- POST /check — body: { "new_drug": "X", "current": ["A","B"], "patient_name": "...", "age": 45 }
- GET /visits — recent checks

## Project layout
- Backend/ — FastAPI app, data, retrieval/normalizer modules
- frontend/ — Streamlit UI (frontend/app.py)
- requirements.txt — Python dependencies

## Notes
- Keep two terminals open when developing (backend + frontend).
- If changing imports to the maintained fork, replace `fuzzywuzzy` with `thefuzz` and update requirements.
