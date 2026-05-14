"""
Compatibility package for running AAJE from the repository root.

The backend code lives in ``backend/app`` and imports modules as ``app.*``.
Adding this small shim lets commands like ``uvicorn app.main:app`` work from
the repo root as well as from the ``backend`` directory.
"""
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = _ROOT / "backend"
_BACKEND_APP = _BACKEND / "app"

if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

__path__ = [str(_BACKEND_APP)]
