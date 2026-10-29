"""
DocuShield Startup Runner
Launches the FastAPI backend and serves the interactive dashboard on http://127.0.0.1:8000
"""
import sys
import os

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import database
import samples_generator
import app
import uvicorn

def main():
    print("=" * 70)
    print("🛡️  DOCUSHIELD: INTELLIGENT DOCUMENT FORGERY DETECTION & VERIFICATION")
    print("   Authors: Vignesh S • Sudharshan • Lavan Kumar")
    print("   M.Tech CSE - Data Science | Cloud Computing")
    print("=" * 70)
    
    # Ensure database initialized
    database.init_db()
    
    # Ensure samples are generated
    sample_dir = os.path.join(BASE_DIR, "sample_data")
    samples_generator.generate_all_samples(sample_dir)

    print("\n🚀 Starting DocuShield Application Server...")
    print("👉 Dashboard URL : http://127.0.0.1:8000")
    print("👉 Swagger Docs  : http://127.0.0.1:8000/docs")
    print("👉 Health API    : http://127.0.0.1:8000/api/health")
    print("\nPress Ctrl+C to stop the server.\n")

    uvicorn.run(app.app, host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    main()
