"""
DocuShield Main ASGI Entrypoint
Enables Render's default start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Import the FastAPI application instance
from app import app
