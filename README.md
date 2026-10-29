# 🛡️ DocuShield: Cloud-Based Intelligent Document Forgery Detection and Verification System

**Working Prototype & Full Project Deliverable**  
**Course:** Cloud Computing • **Program:** M.Tech CSE – Data Science  
**Authors:** Vignesh S • Sudharshan • Lavan Kumar  

---

## 🌟 Quick Start Guide

### 1. Launch the System
Open your PowerShell or Terminal in the project root:
```powershell
cd C:\Users\jetly\.gemini\antigravity\scratch\docushield
python start_server.py
```
*Note: If using standard python path:*
```powershell
& "C:\Users\jetly\AppData\Local\Python\bin\python.exe" start_server.py
```

### 2. Access the Application
- 🖥️ **Web Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- 📑 **Interactive API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 🩺 **Health API:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 📁 Project Structure

```text
docushield/
├── backend/
│   ├── app.py                  # FastAPI REST engine with all 9 project endpoints
│   ├── forensic_engine.py      # PyMuPDF, OpenCV, ELA, SHA-256, Scikit-learn ML pipeline
│   ├── database.py             # SQLite database layer (documents, originals, audit logs)
│   ├── report_generator.py     # ReportLab PDF verification certificate generator
│   ├── samples_generator.py    # Generates synthetic authentic & forged receipt/cert test files
│   └── docushield.db           # SQLite database file
├── frontend/
│   ├── index.html              # Sleek modern dashboard matching Slide 15 & 16
│   ├── app.js                  # Frontend state, API integration & diff visualizer
│   └── style.css               # Dark cyber-aesthetic glassmorphism stylesheet
├── docs/
│   ├── DocuShield_Project_Documentation.pdf # Publication-quality 5-page Academic PDF Report
│   ├── DOCUSHIELD_DOCUMENTATION.md          # Complete Technical & System Architecture manual
│   └── generate_pdf_doc.py                  # ReportLab script that compiles the official PDF
├── sample_data/
│   ├── sample_receipt_original.png          # Master Receipt (Rs. 2,500)
│   ├── sample_receipt_edited.png            # Tampered Receipt (Rs. 9,500 demo)
│   ├── sample_academic_certificate_original.pdf
│   └── sample_academic_certificate_altered.pdf
├── start_server.py             # One-click startup script
└── README.md                   # This guide
```

---

## 🚀 Key Modules & Capabilities

1. **Document Verification Workspace (Slide 15):**
   - Drag & drop ingestion of PDF, PNG, JPG, and JPEG documents.
   - Validation of binary magic signatures and file size bounds (25MB limit).
   - Instant calculation of 64-hex SHA-256 cryptographic fingerprints.
   - One-click sample test buttons for instant testing.

2. **Multi-Layer Forensic Analysis (Slide 18):**
   - **PyMuPDF Document Parser:** Extracts embedded text, metadata (producer, author, creation date), page count, and encryption status.
   - **Laplacian Sharpness Variance:** Computes edge gradient energy ($\sigma^2$) to detect blurry scans or recaptured photos.
   - **Canny Edge Density:** Identifies glyph layout density and anomalies.
   - **Error Level Analysis (ELA):** Exposes differing JPEG compression histories on spliced areas.

3. **Alteration Detection Test (Slide 17):**
   - Side-by-side comparison of original vs edited receipts.
   - Automated contour localization drawing **high-visibility red bounding rectangles** around altered amounts (e.g., Rs. 2,500 changed to Rs. 9,500).

4. **Cryptographic Registry & Audit Trail:**
   - Register authoritative masters with custom labels and categories.
   - Exact byte verification with `MATCH` (Green) or `MISMATCH` (Red) indicators.
   - Relational audit logs stored in SQLite.

5. **Downloadable PDF Verification Certificate (Slide 16):**
   - Real-time generation of tamper-evident verification certificates via ReportLab.
   - Includes document UUID, hashes, forensic scores, extracted text, and reviewer sign-off blocks.

---

## 🧪 Testing the 7-Step Demonstration (Slide 24)

1. Start the server using `python start_server.py`.
2. Open `http://127.0.0.1:8000` in your browser.
3. Click the sample button: **"Original Receipt (Rs 2,500)"**.
4. Click **"Analyze Document"** — inspect the extracted metadata and forensic indicators.
5. In the Verification Action, select **"Register as Reference"** with label *"Master Store Receipt"*.
6. Upload the exact same file again and choose verify — witness the green **`MATCH`** badge.
7. Click **"Edited Receipt (Rs 9,500)"** — witness the red **`MISMATCH`** badge.
8. Switch to the **Visual Alteration Test** tab and click **"Run Synthetic Receipt Demo"** to see the red outline around the altered amount!
9. Click **"Download PDF Verification Report"** to export the official verification certificate.

---

## 👥 Authors
- **Vignesh S**
- **Sudharshan**
- **Lavan Kumar**

*Department of Computer Science & Engineering (Data Science)*  
*Academic Year 2026*
