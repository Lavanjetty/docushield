"""
DocuShield Startup Runner
Launches the FastAPI backend and serves the interactive dashboard.
Compatible with local development and cloud platforms like Render.
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
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print("=" * 70)
    print("🛡️  DOCUSHIELD: INTELLIGENT DOCUMENT FORGERY DETECTION & VERIFICATION")
    print("   Authors: Vignesh S • Sudharshan • Lavan Kumar")
    print("   M.Tech CSE - Data Science | Cloud Computing")
    print("=" * 70)
    
    # Ensure database initialized
    database.init_db()
    
    # Ensure samples are generated
    sample_dir = os.path.join(BASE_DIR, "sample_data")
    try:
        samples_generator.generate_all_samples(sample_dir)
    except Exception as e:
        print(f"Sample generation note: {e}")

    print(f"\n🚀 Starting DocuShield Application Server on {host}:{port}...")
    print(f"👉 Local Dashboard URL : http://127.0.0.1:{port}")
    print(f"👉 Swagger Docs API    : http://127.0.0.1:{port}/docs")
    print(f"👉 Health Check API    : http://127.0.0.1:{port}/api/health")
    print("\nPress Ctrl+C to stop the server.\n")

    uvicorn.run(app.app, host=host, port=port, reload=False)

if __name__ == "__main__":
    main()
