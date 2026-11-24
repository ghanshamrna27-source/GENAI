"""
Root entry point wrapper for Render or root-level deployments.
Redirects to the GitGuru FastAPI application.
"""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent / "GitGuru"
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from app.main import app  # noqa: E402, F401
