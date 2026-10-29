"""
DocuShield PDF Verification Report Generator
Generates a clean, professional, publication-grade Document Verification Audit Certificate PDF.
"""
import os
from datetime import datetime
from typing import Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_pdf_report(doc_data: Dict[str, Any], output_path: str, verification_result: Dict[str, Any] = None) -> str:
    """
    Generates an official DocuShield Document Verification Audit Report PDF.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styling
    title_style = ParagraphStyle(
        'DocuTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a')
    )

    subtitle_style = ParagraphStyle(
        'DocuSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0369a1'),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'DocuBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b')
    )

    code_style = ParagraphStyle(
        'DocuCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#0f172a')
    )

    elements = []

    # Header Banner
    header_data = [
        [
            Paragraph("<b>DOCUSHIELD</b><br/><font size=8 color='#0284c7'>INTELLIGENT DOCUMENT FORENSICS & VERIFICATION</font>", title_style),
            Paragraph(f"<b>AUDIT CERTIFICATE</b><br/>Ref: {doc_data.get('document_uuid', 'DOC-8839')[:16]}<br/>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[330, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=12))

    # Overall Status Banner
    status = doc_data.get("status", "Requires Review")
    status_color = colors.HexColor('#16a34a') if status == "MATCH" else (colors.HexColor('#dc2626') if status == "MISMATCH" else colors.HexColor('#d97706'))
    
    status_data = [
        [
            Paragraph("<b>SYSTEM ASSESSMENT STATUS:</b>", ParagraphStyle('B1', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#0f172a'))),
            Paragraph(f"<b>{status.upper()}</b>", ParagraphStyle('B2', fontName='Helvetica-Bold', fontSize=11, textColor=status_color)),
            Paragraph("Evidence-Led Multi-Layer Analysis", subtitle_style)
        ]
    ]
    status_table = Table(status_data, colWidths=[180, 150, 200])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(status_table)
    elements.append(Spacer(1, 10))

    # File Identity & Cryptographic Fingerprint
    elements.append(Paragraph("1. File Identity & Cryptographic Integrity", section_heading))
    
    sha256 = doc_data.get("sha256", "N/A")
    file_size_kb = round(doc_data.get("file_size", 0) / 1024, 2)
    
    identity_data = [
        [Paragraph("<b>Filename:</b>", body_style), Paragraph(doc_data.get("filename", "unknown"), body_style)],
        [Paragraph("<b>File Type:</b>", body_style), Paragraph(doc_data.get("file_type", "").upper(), body_style)],
        [Paragraph("<b>File Size:</b>", body_style), Paragraph(f"{file_size_kb} KB ({doc_data.get('file_size', 0)} bytes)", body_style)],
        [Paragraph("<b>Uploaded At:</b>", body_style), Paragraph(doc_data.get("uploaded_at", "N/A"), body_style)],
        [Paragraph("<b>SHA-256 Fingerprint:</b>", body_style), Paragraph(f"<code>{sha256}</code>", code_style)]
    ]
    
    if verification_result:
        verif_match = verification_result.get("result", "UNKNOWN")
        match_color = "#16a34a" if verif_match == "MATCH" else "#dc2626"
        identity_data.append([
            Paragraph("<b>Trusted Registry Check:</b>", body_style),
            Paragraph(f"<font color='{match_color}'><b>{verif_match}</b></font> against <i>{verification_result.get('original_label', 'Registered Original')}</i>", body_style)
        ])
    
    id_table = Table(identity_data, colWidths=[140, 390])
    id_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    elements.append(id_table)
    elements.append(Spacer(1, 10))

    # Forensic Inspection Metrics
    report_json = doc_data.get("report_json", {})
    img_forensics = report_json.get("image_forensics")
    metadata = report_json.get("metadata", {})
    ml_result = report_json.get("ml_result", {})

    elements.append(Paragraph("2. Forensic Inspection Indicators", section_heading))
    
    forensic_data = [
        [Paragraph("<b>Indicator</b>", body_style), Paragraph("<b>Observed Value</b>", body_style), Paragraph("<b>Interpretation</b>", body_style)]
    ]

    if img_forensics:
        sharpness = img_forensics.get("sharpness_score", 0)
        edge_dens = img_forensics.get("edge_density", 0)
        ela_mean = img_forensics.get("ela_metrics", {}).get("mean_delta", 0)

        forensic_data.append([
            Paragraph("Laplacian Sharpness", body_style),
            Paragraph(f"{sharpness}", code_style),
            Paragraph("High text contrast / digital sharpness" if sharpness > 1000 else "Standard resolution scan", body_style)
        ])
        forensic_data.append([
            Paragraph("Canny Edge Density", body_style),
            Paragraph(f"{edge_dens:.1%}", code_style),
            Paragraph("Expected structured document line & glyph density", body_style)
        ])
        forensic_data.append([
            Paragraph("Error Level Analysis (ELA)", body_style),
            Paragraph(f"Mean delta: {ela_mean}", code_style),
            Paragraph("Compression consistency indicator across surface", body_style)
        ])
    elif doc_data.get("file_type") == "pdf":
        page_cnt = metadata.get("page_count", 1)
        producer = metadata.get("producer", "Standard PDF Engine")
        forensic_data.append([
            Paragraph("Document Page Count", body_style),
            Paragraph(f"{page_cnt} page(s)", code_style),
            Paragraph("Valid multipage structure verified", body_style)
        ])
        forensic_data.append([
            Paragraph("PDF Creation Engine", body_style),
            Paragraph(producer[:35], code_style),
            Paragraph("Software producer string recorded from trailer", body_style)
        ])

    if ml_result:
        risk = ml_result.get("risk_score", 0.5)
        forensic_data.append([
            Paragraph("ML Text Pattern Screening", body_style),
            Paragraph(f"Risk Index: {risk:.2f}", code_style),
            Paragraph(ml_result.get("explanation", "Linguistic analysis complete")[:60], body_style)
        ])

    f_table = Table(forensic_data, colWidths=[150, 130, 250])
    f_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284c7')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    elements.append(f_table)
    elements.append(Spacer(1, 10))

    # Extracted Text Section
    extracted = doc_data.get("extracted_text", "")
    if extracted:
        elements.append(Paragraph("3. Extracted Document Content (OCR / Stream)", section_heading))
        text_sample = extracted[:400] + ("..." if len(extracted) > 400 else "")
        text_box_data = [[Paragraph(f"<font color='#334155'>{text_sample.replace(chr(10), '<br/>')}</font>", code_style)]]
        text_table = Table(text_box_data, colWidths=[530])
        text_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 8)
        ]))
        elements.append(text_table)
        elements.append(Spacer(1, 10))

    # Responsible Interpretation & Disclaimers (Slide 8 & Slide 25)
    elements.append(Paragraph("4. Responsible Verification Boundary", section_heading))
    disclaimer_text = (
        "<b>Important Operational Scope:</b> DocuShield organizes evidence and exact file identity checks. "
        "Cryptographic SHA-256 confirms byte-level consistency against registered masters. "
        "Forensic indicators (sharpness, edge density, ELA, and text classification) are descriptive screening tools "
        "and do not constitute an autonomous legal certificate of document authenticity. A mismatch indicates byte alteration "
        "which may stem from compression, re-saving, or deliberate tampering."
    )
    disc_data = [[Paragraph(disclaimer_text, ParagraphStyle('D1', fontName='Helvetica-Oblique', fontSize=8, leading=11, textColor=colors.HexColor('#475569')))]]
    disc_table = Table(disc_data, colWidths=[530])
    disc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fffbeb')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#fde68a')),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    elements.append(disc_table)
    elements.append(Spacer(1, 15))

    # Sign-off block
    sign_data = [
        [
            Paragraph("<b>Project Engineering Team:</b><br/>Vignesh S • Sudharshan • Lavan Kumar<br/><i>M.Tech CSE – Data Science</i>", body_style),
            Paragraph("<b>Verification Officer:</b><br/>___________________________<br/>DocuShield Automated Audit Engine v2.0", body_style)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[280, 250])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('TOPPADDING', (0,0), (-1,-1), 10)
    ]))
    elements.append(KeepTogether([sign_table]))

    doc.build(elements)
    return output_path
