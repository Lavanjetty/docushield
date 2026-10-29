"""
DocuShield FastAPI Application
Cloud-Based Intelligent Document Forgery Detection and Verification System
Authors: Vignesh S • Sudharshan • Lavan Kumar (M.Tech CSE - Data Science)
"""
import os
import uuid
import shutil
import json
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Query, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database
import forensic_engine
import report_generator
import samples_generator

app = FastAPI(
    title="DocuShield API",
    description="Intelligent Document Forgery Detection and Verification System REST API",
    version="2.0.0"
)

# Enable CORS for local web interfaces and Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "backend", "uploads")
STATIC_FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
SAMPLE_DATA_DIR = os.path.join(BASE_DIR, "sample_data")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SAMPLE_DATA_DIR, exist_ok=True)

# Mount static files
app.mount("/static/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static/samples", StaticFiles(directory=SAMPLE_DATA_DIR), name="samples")

# Initialize SQLite tables
database.init_db()

# Preload sample originals if empty
def preload_default_originals():
    origs = database.list_trusted_originals()
    if not origs:
        # Check if sample receipt original exists
        sample_rcpt = os.path.join(SAMPLE_DATA_DIR, "sample_receipt_original.png")
        if os.path.exists(sample_rcpt):
            with open(sample_rcpt, "rb") as f:
                content = f.read()
                h = forensic_engine.compute_sha256(content)
                database.insert_trusted_original({
                    "original_uuid": "ORIG-" + uuid.uuid4().hex[:8].upper(),
                    "label": "Store Master Receipt (ROPT-1024 / Rs. 2,500)",
                    "sha256": h,
                    "filename": "sample_receipt_original.png",
                    "category": "Invoices/Receipts",
                    "registered_at": datetime.now().isoformat()
                })
        # Check sample cert
        sample_cert = os.path.join(SAMPLE_DATA_DIR, "sample_academic_certificate_original.pdf")
        if os.path.exists(sample_cert):
            with open(sample_cert, "rb") as f:
                content = f.read()
                h = forensic_engine.compute_sha256(content)
                database.insert_trusted_original({
                    "original_uuid": "ORIG-" + uuid.uuid4().hex[:8].upper(),
                    "label": "University Registrar Transcript (AC-2026-9042)",
                    "sha256": h,
                    "filename": "sample_academic_certificate_original.pdf",
                    "category": "Academic Certificates",
                    "registered_at": datetime.now().isoformat()
                })

preload_default_originals()

@app.get("/api/health")
def get_health():
    """Health check endpoint matching presentation slide 20."""
    return {
        "status": "healthy",
        "service": "DocuShield Verification Engine",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "opencv_available": forensic_engine.OPENCV_AVAILABLE,
        "pymupdf_available": forensic_engine.PYMUPDF_AVAILABLE
    }

@app.post("/api/documents")
async def upload_and_analyze_document(file: UploadFile = File(...)):
    """
    Ingest PDF or image file:
    - Validates magic header signature and file size
    - Calculates exact SHA-256 fingerprint
    - Runs text extraction (PyMuPDF) and image forensics (OpenCV)
    - Saves document record in SQLite
    """
    file_bytes = await file.read()
    filename = file.filename or "unknown_document"

    valid, message, ext = forensic_engine.validate_file(file_bytes, filename)
    if not valid:
        raise HTTPException(status_code=400, detail=message)

    doc_uuid = "DOC-" + uuid.uuid4().hex[:10].upper()
    stored_filename = f"{doc_uuid}_{filename}"
    stored_path = os.path.join(UPLOAD_DIR, stored_filename)

    with open(stored_path, "wb") as f:
        f.write(file_bytes)

    # Execute Forensics Pipeline
    analysis = forensic_engine.analyze_document_pipeline(file_bytes, filename, UPLOAD_DIR)
    if not analysis.get("success"):
        raise HTTPException(status_code=400, detail=analysis.get("error", "Processing failed."))

    doc_record = {
        "document_uuid": doc_uuid,
        "filename": filename,
        "stored_path": stored_path,
        "file_type": ext,
        "uploaded_at": analysis["uploaded_at"],
        "file_size": analysis["file_size"],
        "sha256": analysis["sha256"],
        "status": "Requires Review",
        "extracted_text": analysis.get("extracted_text", ""),
        "report_json": analysis
    }

    doc_id = database.insert_document(doc_record)
    doc_record["id"] = doc_id
    doc_record["file_url"] = f"/static/uploads/{stored_filename}"

    return doc_record

@app.get("/api/documents")
def get_documents(search: Optional[str] = Query(None), limit: int = Query(50)):
    """Search and retrieve document history."""
    docs = database.list_documents(search=search, limit=limit)
    return {"count": len(docs), "documents": docs}

@app.get("/api/documents/{doc_id}")
def get_document_details(doc_id: int):
    """Retrieve full analysis record by document ID."""
    doc = database.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    stored_name = os.path.basename(doc["stored_path"])
    doc["file_url"] = f"/static/uploads/{stored_name}"
    return doc

@app.post("/api/originals")
async def register_trusted_original(
    label: str = Form(...),
    category: str = Form("General"),
    sha256: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Register a trusted original master fingerprint:
    - By direct SHA-256 string, OR
    - By uploading the original reference file
    """
    final_sha256 = ""
    orig_filename = ""

    if file:
        content = await file.read()
        final_sha256 = forensic_engine.compute_sha256(content)
        orig_filename = file.filename or ""
        # Store reference file
        orig_uuid = "ORIG-" + uuid.uuid4().hex[:8].upper()
        ref_path = os.path.join(UPLOAD_DIR, f"{orig_uuid}_{orig_filename}")
        with open(ref_path, "wb") as f:
            f.write(content)
    elif sha256:
        final_sha256 = sha256.strip().lower()
        if len(final_sha256) != 64:
            raise HTTPException(status_code=400, detail="Invalid SHA-256 hash length (must be 64 hexadecimal characters).")
        orig_uuid = "ORIG-" + uuid.uuid4().hex[:8].upper()
    else:
        raise HTTPException(status_code=400, detail="Either file upload or sha256 string must be provided.")

    original_data = {
        "original_uuid": orig_uuid,
        "label": label,
        "sha256": final_sha256,
        "filename": orig_filename,
        "category": category,
        "registered_at": datetime.now().isoformat()
    }

    oid = database.insert_trusted_original(original_data)
    original_data["id"] = oid
    return original_data

@app.get("/api/originals")
def get_trusted_originals():
    """List all registered original masters."""
    origs = database.list_trusted_originals()
    return {"count": len(origs), "trusted_originals": origs}

@app.post("/api/documents/{doc_id}/verify/{original_id}")
def verify_document_against_original(doc_id: int, original_id: int):
    """
    Verifies document against a registered original:
    - Byte-level SHA-256 comparison: MATCH or MISMATCH
    - If both are images, executes pixel alteration diff highlighting
    - Records verification event in audit history
    """
    doc = database.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    orig = database.get_trusted_original_by_id(original_id)
    if not orig:
        raise HTTPException(status_code=404, detail="Trusted original reference not found")

    is_match = (doc["sha256"].lower() == orig["sha256"].lower())
    result_str = "MATCH" if is_match else "MISMATCH"

    diff_info = None
    diff_image_url = None

    # If mismatch and both are images, perform visual alteration analysis
    if not is_match and doc.get("file_type") in ["png", "jpg", "jpeg"]:
        # Find if original file exists in upload dir
        orig_files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(orig["original_uuid"])]
        if orig_files:
            orig_path = os.path.join(UPLOAD_DIR, orig_files[0])
            with open(orig_path, "rb") as f1, open(doc["stored_path"], "rb") as f2:
                diff_filename = f"diff_{doc['document_uuid']}_{orig['original_uuid']}.png"
                diff_output_path = os.path.join(UPLOAD_DIR, diff_filename)
                diff_info = forensic_engine.compare_images_visual(f1.read(), f2.read(), diff_output_path)
                diff_image_url = f"/static/uploads/{diff_filename}"

    verif_record = {
        "document_id": doc["id"],
        "original_id": orig["id"],
        "document_uuid": doc["document_uuid"],
        "original_uuid": orig["original_uuid"],
        "document_name": doc["filename"],
        "original_label": orig["label"],
        "result": result_str,
        "checked_at": datetime.now().isoformat(),
        "details_json": {
            "document_hash": doc["sha256"],
            "original_hash": orig["sha256"],
            "diff_info": diff_info,
            "diff_image_url": diff_image_url,
            "interpretation": "Exact byte match confirmed." if is_match else "SHA-256 mismatch: File bytes differ from registered master."
        }
    }

    vid = database.insert_verification(verif_record)
    verif_record["id"] = vid
    return verif_record

@app.get("/api/history")
def get_verification_history(limit: int = Query(50)):
    """Retrieve all verification history records."""
    history = database.list_verifications(limit=limit)
    return {"count": len(history), "history": history}

@app.get("/api/dashboard")
def get_dashboard_summary():
    """Retrieve aggregate statistics computed directly from SQLite tables."""
    return database.get_dashboard_metrics()

@app.get("/api/documents/{doc_id}/pdf")
def download_verification_pdf(doc_id: int):
    """
    Generates and returns an official verification report PDF
    matching Slide 16 ('document_verification_report.pdf').
    """
    doc = database.get_document_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pdf_filename = f"DocuShield_Audit_{doc['document_uuid']}.pdf"
    pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)

    # Check if there is an associated verification
    history = database.list_verifications(limit=10)
    verif_item = next((h for h in history if h.get("document_uuid") == doc["document_uuid"]), None)

    report_generator.generate_pdf_report(doc, pdf_path, verif_item)
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"verification_report_{doc['filename']}.pdf"
    )

@app.post("/api/compare-images")
async def compare_two_images(
    reference: UploadFile = File(...),
    target: UploadFile = File(...)
):
    """
    Interactive Alteration Detection Test matching Slide 17:
    Visual difference highlighting between original and edited documents.
    """
    ref_bytes = await reference.read()
    tar_bytes = await target.read()

    diff_uuid = uuid.uuid4().hex[:8]
    diff_filename = f"diff_comparison_{diff_uuid}.png"
    diff_path = os.path.join(UPLOAD_DIR, diff_filename)

    diff_result = forensic_engine.compare_images_visual(ref_bytes, tar_bytes, diff_path)
    diff_result["diff_image_url"] = f"/static/uploads/{diff_filename}"

    return diff_result

@app.get("/api/samples")
def list_sample_documents():
    """Returns sample files for immediate one-click testing."""
    samples = []
    if os.path.exists(SAMPLE_DATA_DIR):
        for fname in os.listdir(SAMPLE_DATA_DIR):
            fpath = os.path.join(SAMPLE_DATA_DIR, fname)
            if os.path.isfile(fpath):
                samples.append({
                    "filename": fname,
                    "size_bytes": os.path.getsize(fpath),
                    "url": f"/static/samples/{fname}"
                })
    return {"samples": samples}

@app.get("/")
def serve_index():
    """Serve web dashboard UI."""
    index_path = os.path.join(STATIC_FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "DocuShield API v2.0 is online. Frontend static index not found."}

# Mount frontend directory for assets
if os.path.exists(STATIC_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=STATIC_FRONTEND_DIR, html=True), name="frontend")
