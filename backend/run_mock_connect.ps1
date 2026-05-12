$ErrorActionPreference = "Stop"

$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $BackendDir
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Could not find project virtualenv at $Python"
}

Set-Location $BackendDir
& $Python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --lifespan off
