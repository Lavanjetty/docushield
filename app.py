"""
DocuShield Root ASGI Entrypoint
Enables direct invocation via `uvicorn app:app` or cloud deployment platforms like Render.
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app
