"""
DocuShield SQLite Database Layer
Stores documents, trusted original fingerprints, verification records, and audit logs.
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "docushield.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Documents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_uuid TEXT UNIQUE NOT NULL,
        filename TEXT NOT NULL,
        stored_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        uploaded_at TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        sha256 TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Requires Review',
        extracted_text TEXT DEFAULT '',
        report_json TEXT DEFAULT '{}'
    )
    """)

    # 2. Trusted Originals Registry Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trusted_originals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_uuid TEXT UNIQUE NOT NULL,
        label TEXT NOT NULL,
        sha256 TEXT NOT NULL,
        filename TEXT DEFAULT '',
        category TEXT DEFAULT 'General',
        registered_at TEXT NOT NULL
    )
    """)

    # 3. Verifications History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        original_id INTEGER,
        document_uuid TEXT NOT NULL,
        original_uuid TEXT NOT NULL,
        document_name TEXT NOT NULL,
        original_label TEXT NOT NULL,
        result TEXT NOT NULL,
        checked_at TEXT NOT NULL,
        details_json TEXT DEFAULT '{}',
        FOREIGN KEY (document_id) REFERENCES documents(id),
        FOREIGN KEY (original_id) REFERENCES trusted_originals(id)
    )
    """)

    # 4. Audit Trail Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT,
        timestamp TEXT NOT NULL,
        details TEXT DEFAULT ''
    )
    """)

    conn.commit()
    conn.close()

def log_audit(action: str, entity_type: str, entity_id: str, details: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (action, entity_type, entity_id, timestamp, details) VALUES (?, ?, ?, ?, ?)",
        (action, entity_type, str(entity_id), datetime.now().isoformat(), details)
    )
    conn.commit()
    conn.close()

def insert_document(doc_data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO documents (
            document_uuid, filename, stored_path, file_type,
            uploaded_at, file_size, sha256, status, extracted_text, report_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_data["document_uuid"],
        doc_data["filename"],
        doc_data["stored_path"],
        doc_data["file_type"],
        doc_data["uploaded_at"],
        doc_data["file_size"],
        doc_data["sha256"],
        doc_data.get("status", "Requires Review"),
        doc_data.get("extracted_text", ""),
        json.dumps(doc_data.get("report_json", {}))
    ))
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    log_audit("DOCUMENT_UPLOAD", "document", doc_data["document_uuid"], f"File: {doc_data['filename']}")
    return doc_id

def get_document_by_id(doc_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["report_json"] = json.loads(d["report_json"]) if d["report_json"] else {}
        return d
    return None

def get_document_by_uuid(doc_uuid: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE document_uuid = ?", (doc_uuid,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d["report_json"] = json.loads(d["report_json"]) if d["report_json"] else {}
        return d
    return None

def list_documents(search: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if search:
        query = "%" + search.strip() + "%"
        cursor.execute("""
            SELECT id, document_uuid, filename, file_type, uploaded_at, file_size, sha256, status, 
                   substr(extracted_text, 1, 120) as preview_text
            FROM documents 
            WHERE filename LIKE ? OR sha256 LIKE ? OR extracted_text LIKE ?
            ORDER BY id DESC LIMIT ?
        """, (query, query, query, limit))
    else:
        cursor.execute("""
            SELECT id, document_uuid, filename, file_type, uploaded_at, file_size, sha256, status,
                   substr(extracted_text, 1, 120) as preview_text
            FROM documents 
            ORDER BY id DESC LIMIT ?
        """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_trusted_original(original_data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO trusted_originals (original_uuid, label, sha256, filename, category, registered_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        original_data["original_uuid"],
        original_data["label"],
        original_data["sha256"],
        original_data.get("filename", ""),
        original_data.get("category", "General"),
        original_data["registered_at"]
    ))
    oid = cursor.lastrowid
    conn.commit()
    conn.close()
    log_audit("REGISTER_ORIGINAL", "trusted_original", original_data["original_uuid"], f"Label: {original_data['label']}")
    return oid

def list_trusted_originals() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trusted_originals ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_trusted_original_by_id(oid: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trusted_originals WHERE id = ?", (oid,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def insert_verification(verif_data: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO verifications (
            document_id, original_id, document_uuid, original_uuid,
            document_name, original_label, result, checked_at, details_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        verif_data.get("document_id"),
        verif_data.get("original_id"),
        verif_data["document_uuid"],
        verif_data["original_uuid"],
        verif_data["document_name"],
        verif_data["original_label"],
        verif_data["result"],
        verif_data["checked_at"],
        json.dumps(verif_data.get("details_json", {}))
    ))
    vid = cursor.lastrowid
    conn.commit()
    conn.close()
    log_audit("VERIFY_DOCUMENT", "verification", str(vid), f"Result: {verif_data['result']}")
    return vid

def list_verifications(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM verifications ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        d["details_json"] = json.loads(d["details_json"]) if d["details_json"] else {}
        res.append(d)
    return res

def get_dashboard_metrics() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM documents")
    total_docs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trusted_originals")
    total_originals = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM verifications")
    total_verifications = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM verifications WHERE result = 'MATCH'")
    matches = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM verifications WHERE result = 'MISMATCH'")
    mismatches = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, COUNT(*) FROM documents GROUP BY status")
    status_counts = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    match_rate = round((matches / total_verifications * 100), 1) if total_verifications > 0 else 0.0
    
    return {
        "total_documents": total_docs,
        "total_originals": total_originals,
        "total_verifications": total_verifications,
        "matches": matches,
        "mismatches": mismatches,
        "match_rate_percent": match_rate,
        "status_distribution": status_counts
    }
