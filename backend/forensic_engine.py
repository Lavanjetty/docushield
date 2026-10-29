"""
DocuShield Forensic Engine
Handles cryptographic fingerprinting, PDF inspection, image forensic heuristics (Laplacian sharpness, Canny edge density, ELA), visual difference highlighting, and explainable ML screening.
"""
import os
import io
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List

from PIL import Image, ImageChops, ImageEnhance
import numpy as np

# PyMuPDF
try:
    import pymupdf as fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import fitz
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False

# OpenCV
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# Scikit-learn for text/document pattern screening
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Allowed magic bytes for file validation
MAGIC_SIGNATURES = {
    "pdf": b"%PDF-",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff"
}

class DocumentMLClassifier:
    """Baseline Scikit-learn model trained on document pattern signals."""
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        self.model = LogisticRegression(max_iter=200)
        self.is_trained = False
        self._bootstrap_model()

    def _bootstrap_model(self):
        # Synthetic document corpus representing typical authentic vs tampered/anomaly patterns
        corpus = [
            # Authentic patterns
            "official tax invoice total amount paid received authorized signature company reg gst valid receipt",
            "university degree completion certificate conferred bachelor of science registrar seal academic records",
            "employment offer letter salary components benefits standard legal terms human resources approved",
            "bank account statement monthly transactions opening balance closing balance verified bank stamp",
            "identity card government authority permanent account number date of birth valid identity",
            "purchase order vendor delivery slip item description unit price subtotal tax total confirmed",
            # Manipulated / anomaly patterns
            "demo amount edited altered invoice modified total replacement paste mismatched font size",
            "tampered certificate changed marks revised grade duplicated text layer artifact forged seal",
            "unauthorized modification spliced photo patched address signature copied across layers",
            "altered receipt inflated price patched payment status dummy stamp overwritten text",
            "duplicate serial number inconsistent date format mismatched invoice total calculation error",
            "overlayed text box pasted logo inconsistent resolution blurred background behind numbers"
        ]
        labels = [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1]  # 0: Standard/Authentic, 1: Anomaly-indicative
        
        X = self.vectorizer.fit_transform(corpus)
        self.model.fit(X, labels)
        self.is_trained = True

    def predict(self, text: str) -> Dict[str, Any]:
        if not text or len(text.strip()) < 10:
            return {
                "status": "Inconclusive",
                "risk_score": 0.50,
                "confidence": 0.50,
                "label": "Requires Review",
                "explanation": "Insufficient extracted text to perform statistical linguistic evaluation."
            }
        
        vec = self.vectorizer.transform([text])
        proba = self.model.predict_proba(vec)[0]
        anomaly_risk = float(proba[1])
        
        if anomaly_risk > 0.65:
            label = "Suspicious Anomaly Indicators"
            explanation = "Extracted textual terms overlap with vocabulary frequently observed in altered/edited templates."
        elif anomaly_risk < 0.35:
            label = "Consistent Document Pattern"
            explanation = "Extracted textual phrasing aligns with standard formal invoice, certificate, or statement structures."
        else:
            label = "Neutral / Requires Review"
            explanation = "Text pattern shows standard distribution with no definitive linguistic bias."

        return {
            "status": "Evaluated",
            "risk_score": round(anomaly_risk, 4),
            "confidence": round(float(np.max(proba)), 4),
            "label": label,
            "explanation": explanation
        }

# Global ML instance
ml_classifier = DocumentMLClassifier()

def compute_sha256(file_bytes: bytes) -> str:
    """Computes exact 64-hex SHA-256 fingerprint."""
    hasher = hashlib.sha256()
    hasher.update(file_bytes)
    return hasher.hexdigest()

def validate_file(file_bytes: bytes, filename: str) -> Tuple[bool, str, str]:
    """Validates extension and binary magic signature."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ["pdf", "png", "jpg", "jpeg"]:
        return False, f"Unsupported file extension: .{ext}", ext
    
    if len(file_bytes) == 0:
        return False, "File is empty (0 bytes).", ext
    
    if len(file_bytes) > 25 * 1024 * 1024:
        return False, "File exceeds maximum size limit (25 MB).", ext

    # Validate Magic Signature
    if ext == "pdf":
        if not file_bytes.startswith(b"%PDF-"):
            return False, "Invalid PDF magic signature header.", ext
    elif ext == "png":
        if not file_bytes.startswith(MAGIC_SIGNATURES["png"]):
            return False, "Invalid PNG magic signature header.", ext
    elif ext in ["jpg", "jpeg"]:
        if not file_bytes[:3] == b"\xff\xd8\xff":
            return False, "Invalid JPEG magic signature header.", ext

    return True, "File header signature valid.", ext

def extract_pdf_data(file_bytes: bytes, max_pages: int = 50) -> Dict[str, Any]:
    """Extracts text, page count, and metadata using PyMuPDF."""
    text_content = []
    metadata = {}
    rendered_first_page_path = None

    if not PYMUPDF_AVAILABLE:
        return {
            "status": "PyMuPDF not available",
            "page_count": 0,
            "metadata": {},
            "extracted_text": ""
        }

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        effective_pages = min(page_count, max_pages)

        # Document metadata
        meta = doc.metadata or {}
        metadata = {
            "title": meta.get("title", "") or "Untitled",
            "author": meta.get("author", "") or "Not specified",
            "subject": meta.get("subject", "") or "None",
            "creator": meta.get("creator", "") or "Unknown software",
            "producer": meta.get("producer", "") or "Unknown producer",
            "creation_date": meta.get("creationDate", "") or "N/A",
            "mod_date": meta.get("modDate", "") or "N/A",
            "page_count": page_count,
            "encrypted": doc.is_encrypted,
            "format": "PDF-1." + str(doc.pdf_version() if hasattr(doc, 'pdf_version') else "x")
        }

        # Extract text from pages
        for i in range(effective_pages):
            page = doc.load_page(i)
            text_content.append(page.get_text())

        full_text = "\n\n".join(text_content).strip()
        doc.close()

        return {
            "status": "Success",
            "page_count": page_count,
            "metadata": metadata,
            "extracted_text": full_text
        }
    except Exception as e:
        return {
            "status": f"Error parsing PDF: {str(e)}",
            "page_count": 0,
            "metadata": {},
            "extracted_text": ""
        }

def compute_image_forensics(img_bytes: bytes) -> Dict[str, Any]:
    """
    Computes visual forensic indicators:
    - Laplacian sharpness variance
    - Canny edge density
    - Error Level Analysis (ELA) score
    - Image dimensions and metadata
    """
    pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    width, height = pil_img.size
    np_img = np.array(pil_img)

    # 1. Laplacian Sharpness Variance
    sharpness = 0.0
    edge_density = 0.0
    
    if OPENCV_AVAILABLE:
        gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = float(laplacian.var())

        # 2. Canny Edge Density
        edges = cv2.Canny(gray, 100, 200)
        edge_density = float(np.sum(edges > 0) / (width * height))
    else:
        # High quality numpy fallback
        gray = np.dot(np_img[...,:3], [0.2989, 0.5870, 0.1140])
        # Simple laplacian kernel
        kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        from scipy.signal import convolve2d
        conv = convolve2d(gray, kernel, mode='valid')
        sharpness = float(np.var(conv))
        edge_density = float(np.mean(np.abs(conv) > 30))

    # 3. Error Level Analysis (ELA)
    # Resave at JPEG quality 90 to compute compression delta
    ela_buffer = io.BytesIO()
    pil_img.save(ela_buffer, 'JPEG', quality=90)
    ela_buffer.seek(0)
    recompressed = Image.open(ela_buffer).convert("RGB")

    diff = ImageChops.difference(pil_img, recompressed)
    diff_np = np.array(diff)
    ela_mean_delta = float(np.mean(diff_np))
    ela_max_delta = float(np.max(diff_np))

    # Formulate forensic findings
    findings = []
    if sharpness < 100:
        findings.append("Low Laplacian sharpness: Document image appears blurry, re-photographed, or low-resolution.")
    elif sharpness > 1500:
        findings.append("High Laplacian sharpness: Distinct, high-contrast text and edges characteristic of digital rendering.")
    else:
        findings.append("Moderate Laplacian sharpness: Consistent with normal desktop/flatbed scan.")

    if edge_density > 0.08:
        findings.append(f"High edge density ({edge_density:.1%}): Dense text or complex graphical background.")
    else:
        findings.append(f"Standard edge density ({edge_density:.1%}): Normal sparse document layout.")

    if ela_mean_delta > 8.0:
        findings.append(f"Elevated ELA delta ({ela_mean_delta:.2f}): Noticeable compression discrepancy; possible multi-generation compression or spliced imagery.")
    else:
        findings.append(f"Uniform ELA profile ({ela_mean_delta:.2f}): Compression history is relatively uniform across the document.")

    return {
        "dimensions": {"width": width, "height": height},
        "color_channels": 3,
        "sharpness_score": round(sharpness, 2),
        "edge_density": round(edge_density, 4),
        "ela_metrics": {
            "mean_delta": round(ela_mean_delta, 2),
            "max_delta": round(ela_max_delta, 2)
        },
        "findings": findings
    }

def generate_ela_image(input_bytes: bytes, output_path: str, scale: int = 15):
    """Generates an enhanced Error Level Analysis (ELA) visualization file."""
    original = Image.open(io.BytesIO(input_bytes)).convert("RGB")
    buf = io.BytesIO()
    original.save(buf, 'JPEG', quality=90)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")
    
    diff = ImageChops.difference(original, recompressed)
    # Brighten differences for visual inspection
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema]) if extrema else 1
    if max_diff == 0:
        max_diff = 1
    scale = 255.0 / max_diff
    diff = ImageEnhance.Brightness(diff).enhance(scale)
    diff.save(output_path)

def compare_images_visual(ref_bytes: bytes, target_bytes: bytes, diff_output_path: str) -> Dict[str, Any]:
    """
    Performs pixel-level alignment & difference inspection between reference and target.
    Highlights modified bounding boxes (e.g., altered Rs. 2,500 -> Rs. 9,500 demo).
    """
    img1 = Image.open(io.BytesIO(ref_bytes)).convert("RGB")
    img2 = Image.open(io.BytesIO(target_bytes)).convert("RGB")

    # Resize img2 to img1 if dimensions differ slightly
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)

    arr1 = np.array(img1)
    arr2 = np.array(img2)

    diff_arr = np.abs(arr1.astype(np.int32) - arr2.astype(np.int32))
    diff_magnitude = np.mean(diff_arr, axis=2).astype(np.uint8)

    altered_regions = []
    highlight_img = arr2.copy()

    if OPENCV_AVAILABLE:
        # Threshold difference
        _, thresh = cv2.threshold(diff_magnitude, 25, 255, cv2.THRESH_BINARY)
        # Dilate to connect nearby character differences
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            area = cv2.contourArea(c)
            if area > 40:  # filter noise
                x, y, w, h = cv2.boundingRect(c)
                altered_regions.append({
                    "x": int(x), "y": int(y), "width": int(w), "height": int(h), "area": int(area)
                })
                # Draw high-visibility red rectangle and transparent fill
                cv2.rectangle(highlight_img, (x - 4, y - 4), (x + w + 4, y + h + 4), (255, 0, 50), 3)

        # Save highlighted comparison result
        out_bgr = cv2.cvtColor(highlight_img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(diff_output_path, out_bgr)
    else:
        # PIL fallback
        diff_img = Image.fromarray(diff_magnitude)
        diff_img.save(diff_output_path)

    has_differences = len(altered_regions) > 0
    percent_differing = float(np.sum(diff_magnitude > 25) / diff_magnitude.size) * 100.0

    return {
        "status": "Comparison Complete",
        "has_differences": has_differences,
        "altered_regions_count": len(altered_regions),
        "differing_pixels_percentage": round(percent_differing, 3),
        "bounding_boxes": altered_regions,
        "interpretation": "Pixel-level differences detected between images. Highlighted regions outline modified or displaced visual elements." if has_differences else "No significant visual pixel discrepancies detected."
    }

def analyze_document_pipeline(file_bytes: bytes, filename: str, storage_dir: str) -> Dict[str, Any]:
    """
    Unified Document Ingestion and Forensics Pipeline.
    Implements all steps from Project Proposal & Presentation:
    1. Validation
    2. SHA-256 fingerprinting
    3. Metadata & Text extraction
    4. Image forensics (Laplacian, edge density, ELA)
    5. ML text-pattern screening
    6. Explainable evaluation
    """
    valid, message, ext = validate_file(file_bytes, filename)
    if not valid:
        return {
            "success": False,
            "error": message
        }

    sha256_hash = compute_sha256(file_bytes)
    file_size = len(file_bytes)
    now_iso = datetime.now().isoformat()

    extracted_text = ""
    metadata = {}
    image_forensics = None
    ela_rel_path = None

    if ext == "pdf":
        pdf_res = extract_pdf_data(file_bytes)
        extracted_text = pdf_res.get("extracted_text", "")
        metadata = pdf_res.get("metadata", {})
        metadata["file_type"] = "PDF"
        metadata["extension"] = ext
    else:
        # Image pipeline
        image_forensics = compute_image_forensics(file_bytes)
        metadata = {
            "file_type": "Image",
            "extension": ext,
            "dimensions": f"{image_forensics['dimensions']['width']}x{image_forensics['dimensions']['height']}",
            "color_channels": 3,
            "size_bytes": file_size
        }
        
        # Save ELA visualization
        ela_filename = f"ela_{sha256_hash[:12]}.jpg"
        ela_full_path = os.path.join(storage_dir, ela_filename)
        generate_ela_image(file_bytes, ela_full_path)
        ela_rel_path = f"/static/uploads/{ela_filename}"

    # ML Classifier Screening
    ml_result = ml_classifier.predict(extracted_text)

    # Explainable Assessment Synthesizer
    all_findings = []
    if image_forensics:
        all_findings.extend(image_forensics.get("findings", []))
    
    if ext == "pdf":
        if not metadata.get("author") or metadata.get("author") == "Not specified":
            all_findings.append("PDF author metadata is omitted or stripped.")
        if metadata.get("creator") and "unknown" not in metadata.get("creator").lower():
            all_findings.append(f"Produced via software: {metadata.get('creator')}")

    all_findings.append(f"Linguistic pattern result: {ml_result['explanation']}")

    # Decision Boundary rule (per Slide 8):
    # Organizes evidence without declaring file authentic or forged purely from weak heuristics.
    assessment = {
        "status": "Requires Review",
        "integrity_rule": "Exact file identity is strictly verifiable only when evaluated against a registered SHA-256 fingerprint.",
        "findings": all_findings,
        "recommendation": "Examine extracted textual fields and verify against official registry or issuer records."
    }

    return {
        "success": True,
        "filename": filename,
        "file_size": file_size,
        "sha256": sha256_hash,
        "file_type": ext,
        "uploaded_at": now_iso,
        "metadata": metadata,
        "extracted_text": extracted_text,
        "image_forensics": image_forensics,
        "ela_image_url": ela_rel_path,
        "ml_result": ml_result,
        "assessment": assessment
    }
