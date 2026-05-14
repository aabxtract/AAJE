Local testing with SQLite (quick)

1) Create & activate venv

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate
pip install --upgrade pip
```

2) Install requirements (we removed heavy native deps)

```powershell
pip install -r requirements.txt
pip install aiosqlite
```

3) Ensure `.env` sets `DATABASE_URL` for SQLite (already configured):

```
DATABASE_URL=sqlite+aiosqlite:///./aaje_dev.db
```

4) Run the end-to-end simulation (creates store, product, order, simulates payment):

```powershell
$env:PYTHONPATH='backend'
python backend/scripts/run_end_to_end.py
```

5) Run the API server to browse storefront pages:

```powershell
$env:PYTHONPATH='backend'
uvicorn app.main:app --reload --port 8000
# Open http://localhost:8000/health
# Visit a store: http://localhost:8000/store/{slug}
```

Notes:
- We removed `pyiceberg` from `requirements.txt` to avoid MSVC build issues on Windows. If you need `pyiceberg`, install Visual C++ Build Tools and re-add the dependency.
- This SQLite setup is for local dev and testing only. For production parity use Postgres; switch `DATABASE_URL` back to a Postgres DSN and restore Postgres-specific model settings if you previously reverted them.
