"""
DocuShield Sample Data Generator
Generates synthetic sample documents matching the presentation:
- Original Receipt (Rs. 2,500)
- Edited Receipt (Rs. 9,500)
- Authentic Academic Certificate (PDF)
- Altered Academic Certificate (PDF)
"""
import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_sample_receipt(output_path: str, amount_str: str = "Rs. 2,500", note: str = ""):
    """Generates a clean synthetic store receipt image."""
    width, height = 480, 560
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Simple clean styling
    # Header
    draw.rectangle([0, 0, width, 60], fill=(15, 23, 42))
    draw.text((140, 18), "DOCUSHIELD RETAIL STORE", fill=(255, 255, 255))

    y = 80
    draw.text((40, y), "Receipt No: ROPT-1024", fill=(30, 41, 59))
    y += 25
    draw.text((40, y), "Date: 2026-10-29 14:30 IST", fill=(71, 85, 105))
    y += 25
    draw.text((40, y), "Cashier: Register Terminal 04", fill=(71, 85, 105))
    y += 25
    draw.line([(40, y), (440, y)], fill=(203, 213, 225), width=2)
    y += 15

    # Line Items
    draw.text((40, y), "Item Description", fill=(15, 23, 42))
    draw.text((360, y), "Total", fill=(15, 23, 42))
    y += 25
    draw.text((40, y), "1x Laptop Messenger Bag", fill=(51, 65, 85))
    draw.text((360, y), amount_str, fill=(51, 65, 85))
    y += 25
    draw.text((40, y), "Tax (GST 18% Included)", fill=(100, 116, 139))
    y += 35
    draw.line([(40, y), (440, y)], fill=(203, 213, 225), width=2)
    y += 15

    # Total Amount
    draw.text((40, y), "FINAL AMOUNT PAID:", fill=(15, 23, 42))
    draw.text((340, y), amount_str, fill=(2, 132, 199))
    y += 35
    draw.text((40, y), "Payment Method: UPI / Instant Settlement", fill=(71, 85, 105))
    y += 25
    draw.text((40, y), "Transaction Status: SUCCESSFUL - PAID", fill=(22, 163, 74))
    
    if note:
        y += 35
        draw.rectangle([40, y, 440, y + 30], fill=(254, 242, 242), outline=(239, 68, 68))
        draw.text((55, y + 8), f"NOTE: {note}", fill=(185, 28, 28))

    # Footer
    y = 500
    draw.line([(40, y), (440, y)], fill=(226, 232, 240), width=1)
    draw.text((110, y + 15), "Thank you for shopping with DocuShield Store!", fill=(148, 163, 184))

    img.save(output_path, "PNG")

def generate_sample_certificate(output_path: str, student_name: str, cgpa: str, status_msg: str):
    """Generates an academic certificate PDF."""
    doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()

    elements = []

    title = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=22, alignment=1, textColor=colors.HexColor('#0f172a'))
    sub = ParagraphStyle('S', fontName='Helvetica', fontSize=12, alignment=1, textColor=colors.HexColor('#475569'), spaceBefore=8, spaceAfter=20)
    body = ParagraphStyle('B', fontName='Helvetica', fontSize=11, leading=16, alignment=1, textColor=colors.HexColor('#1e293b'))

    elements.append(Paragraph("<b>INSTITUTE OF ADVANCED COMPUTING & SCIENCE</b>", title))
    elements.append(Paragraph("OFFICIAL ACADEMIC TRANSCRIPT & VERIFICATION RECORD", sub))
    elements.append(Spacer(1, 15))

    cert_text = (
        f"This is to certify that <b>{student_name}</b>, Registration Number <b>AC-2026-9042</b>, "
        f"has successfully satisfied all curriculum requirements for the degree of:<br/><br/>"
        f"<b>Master of Technology in Computer Science & Engineering</b><br/>"
        f"<i>Specialization: Data Science & Cloud Computing</i><br/><br/>"
        f"Cumulative Grade Point Average (CGPA): <b>{cgpa} / 10.00</b><br/>"
        f"Classification: <b>{status_msg}</b>"
    )
    elements.append(Paragraph(cert_text, body))
    elements.append(Spacer(1, 40))

    footer_data = [
        [
            Paragraph("<b>Dean of Academic Affairs</b><br/>Prof. R. Srinivasan", ParagraphStyle('F1', fontName='Helvetica', fontSize=9, alignment=0)),
            Paragraph("<b>Controller of Examinations</b><br/>Dr. M. K. Narayanan", ParagraphStyle('F2', fontName='Helvetica', fontSize=9, alignment=2))
        ]
    ]
    footer_table = Table(footer_data, colWidths=[250, 250])
    elements.append(footer_table)

    doc.build(elements)

def generate_all_samples(target_dir: str):
    os.makedirs(target_dir, exist_ok=True)
    
    # Receipts
    orig_receipt = os.path.join(target_dir, "sample_receipt_original.png")
    edited_receipt = os.path.join(target_dir, "sample_receipt_edited.png")
    generate_sample_receipt(orig_receipt, "Rs. 2,500")
    generate_sample_receipt(edited_receipt, "Rs. 9,500", note="DEMO AMOUNT EDITED FOR FORGERY TESTING")

    # Certificates
    orig_cert = os.path.join(target_dir, "sample_academic_certificate_original.pdf")
    altered_cert = os.path.join(target_dir, "sample_academic_certificate_altered.pdf")
    generate_sample_certificate(orig_cert, "Sudharshan", "8.95", "First Class with Distinction")
    generate_sample_certificate(altered_cert, "Sudharshan", "9.95", "Altered CGPA Test Record")

    print(f"Generated sample files in: {target_dir}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(os.path.dirname(current_dir), "sample_data")
    generate_all_samples(sample_dir)
