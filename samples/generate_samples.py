import os
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont, ImageChops
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_clean_pdf(filename):
    print(f"Generating clean PDF: {filename}")
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=15
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )
    
    body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.white
    )

    # Header section
    story.append(Paragraph("APEX GLOBAL SOLUTIONS INC.", body_bold))
    story.append(Paragraph("100 Enterprise Way, Suite 400, Silicon Valley, CA 94089", body_style))
    story.append(Spacer(1, 15))
    
    # Document Title
    story.append(Paragraph("OFFICIAL PAYSLIP", title_style))
    story.append(Spacer(1, 10))
    
    # Employee details table
    details_data = [
        [Paragraph("<b>Employee Name:</b>", body_style), Paragraph("John Doe", body_style),
         Paragraph("<b>Pay Period:</b>", body_style), Paragraph("May 01, 2026 - May 31, 2026", body_style)],
        [Paragraph("<b>Employee ID:</b>", body_style), Paragraph("EMP-2026-9876", body_style),
         Paragraph("<b>Payment Date:</b>", body_style), Paragraph("May 29, 2026", body_style)],
        [Paragraph("<b>Department:</b>", body_style), Paragraph("Risk Advisory", body_style),
         Paragraph("<b>Bank Account:</b>", body_style), Paragraph("Apex Bank ****5678", body_style)]
    ]
    
    details_table = Table(details_data, colWidths=[110, 150, 100, 160])
    details_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(details_table)
    story.append(Spacer(1, 20))
    
    # Salary breakdown table
    salary_data = [
        [Paragraph("Earnings / Allowances", header_style), Paragraph("Amount", header_style),
         Paragraph("Deductions", header_style), Paragraph("Amount", header_style)],
        [Paragraph("Basic Salary", body_style), Paragraph("$5,000.00", body_style),
         Paragraph("Federal Tax", body_style), Paragraph("$500.00", body_style)],
        [Paragraph("House Rent Allowance", body_style), Paragraph("$800.00", body_style),
         Paragraph("State Tax", body_style), Paragraph("$200.00", body_style)],
        [Paragraph("Special Allowance", body_style), Paragraph("$400.00", body_style),
         Paragraph("Health Insurance", body_style), Paragraph("$100.00", body_style)],
        [Paragraph("Total Earnings", body_bold), Paragraph("$6,200.00", body_bold),
         Paragraph("Total Deductions", body_bold), Paragraph("$800.00", body_bold)]
    ]
    
    salary_table = Table(salary_data, colWidths=[160, 100, 160, 100])
    salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,-1), (1,-1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (2,-1), (3,-1), colors.HexColor('#F8FAFC')),
    ]))
    
    story.append(salary_table)
    story.append(Spacer(1, 25))
    
    # Net Pay Summary Box
    net_pay_data = [
        [Paragraph("<b>NET PAY (A - B)</b>", ParagraphStyle('NetPayLbl', parent=body_bold, fontSize=12, textColor=colors.HexColor('#0F172A'))),
         Paragraph("<b>$5,400.00</b>", ParagraphStyle('NetPayVal', parent=body_bold, fontSize=14, textColor=colors.HexColor('#16A34A')))]
    ]
    net_pay_table = Table(net_pay_data, colWidths=[260, 260])
    net_pay_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#DCFCE7')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#22C55E')),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
    ]))
    
    story.append(net_pay_table)
    story.append(Spacer(1, 40))
    
    # Signatures
    sig_data = [
        [
            Paragraph("Prepared by: HR Operations<br/><br/><i>Jane Smith</i><br/>_______________________", body_style),
            Paragraph("Verified by: Finance Dept<br/><br/><b>[ SECURE STAMP: VERIFIED ]</b><br/>_______________________", ParagraphStyle('SigStamp', parent=body_style, textColor=colors.HexColor('#1D4ED8')))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[260, 260])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(sig_table)
    
    # Build document
    doc.build(story)
    print("Clean PDF generated successfully.")

def generate_tampered_pdf(clean_pdf, output_pdf):
    print(f"Generating tampered PDF from: {clean_pdf} to {output_pdf}")
    # 1. Rasterize clean PDF page 0 to an image using PyMuPDF
    doc = fitz.open(clean_pdf)
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=150)  # Render at 150 DPI for good text rendering
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # Save a copy as JPEG quality 75 to act as the base grid for ELA
    temp_jpeg = "temp_clean_75.jpg"
    img.save(temp_jpeg, "JPEG", quality=75)
    
    # Reload the JPEG image to perform edits on top of the 75 quality grid
    edited_img = Image.open(temp_jpeg).convert("RGB")
    draw = ImageDraw.Draw(edited_img)
    
    # Let's find default font to write with
    try:
        font = ImageFont.truetype("Arial.ttf", 20)
        font_bold = ImageFont.truetype("Arial.ttf", 22)
    except IOError:
        font = ImageFont.load_default()
        font_bold = ImageFont.load_default()
        
    # 2. OVERWRITE BASIC SALARY
    # Basic Salary is located around y-coordinates in the table
    # Coordinates are dependent on 150 DPI. Let's find exact coordinates by testing or draw relative.
    # At 150 DPI, page size is letter: 8.5 * 150 = 1275 wide, 11 * 150 = 1650 tall.
    # Let's cover the Basic Salary amount area and Net Pay amount area.
    # Basic Salary is around x=330, y=550 at 150 DPI (we will draw a white box and replace it).
    # Net Pay is around x=650, y=950.
    # Let's make sure our coordinate assumptions align, or print out dimensions.
    width, height = edited_img.size
    print(f"Rendered image size: {width}x{height}")
    
    # Box for Basic Salary "$5,000.00"
    # Let's draw white rectangle over it
    # We can search coordinates. Let's estimate:
    # Basic Salary label is on the left, amount is at col 1.
    # Col 0: 0 to 160. Col 1: 160 to 260. (In PDF pts: total width 532).
    # At 150 DPI, 1 pt = 150 / 72 = 2.08 pixels.
    # Page margins: leftMargin=40 pts -> 40 * 2.08 = 83 pixels.
    # Table start: y-offset is around 400 pts -> 830 pixels.
    # Let's paint over the Basic Salary amount:
    # Column 1 starts at leftMargin + colWidth0 = 40 + 160 = 200 pt -> 416 pixels.
    # Row 1 (Basic Salary): y is around 250 pt from top -> 520 pixels.
    # Let's white-out Basic Salary and draw "$15,000.00"
    draw.rectangle([415, 480, 520, 520], fill=(255, 255, 255))
    draw.text((415, 485), "$15,000.00", fill=(51, 65, 85), font=font)
    
    # 3. OVERWRITE NET PAY
    # Net Pay summary box is around center-right
    # Let's paint a light green rectangle (to match the Net Pay box background #DCFCE7)
    # The box is DCFCE7, border is 22C55E. Let's paint with DCFCE7.
    # Green fill is (220, 252, 231).
    # Net Pay value is at x=700, y=860.
    draw.rectangle([700, 840, 950, 895], fill=(220, 252, 231))
    draw.text((700, 845), "$15,400.00", fill=(22, 163, 74), font=font_bold)
    
    # 4. COPY-MOVE FORGERY (Stamp duplication)
    # Let's copy the secure stamp "[ SECURE STAMP: VERIFIED ]" from the bottom right
    # and paste it at the top right as a second duplicate verification stamp.
    # Stamp area at bottom right: x=700 to 1050, y=1050 to 1150.
    # Let's crop it and paste it at x=750, y=100.
    stamp_crop = edited_img.crop((700, 1020, 1080, 1080))
    edited_img.paste(stamp_crop, (700, 150))
    
    # Also let's draw a line to show we modified it
    # We can save it as PDF
    # In PyMuPDF we can write the image back to a PDF page.
    edited_img.save("temp_tampered_90.jpg", "JPEG", quality=90)
    
    # Convert JPEG to PDF using PyMuPDF
    img_doc = fitz.open()
    # Use standard letter size (612 x 792 points) to match the clean PDF
    page = img_doc.new_page(width=612, height=792)
    page.insert_image(page.rect, filename="temp_tampered_90.jpg")
    
    # Let's modify the metadata of the tampered PDF to simulate a modified file
    # and to trigger metadata checks.
    metadata = img_doc.metadata
    metadata['creator'] = 'iLovePDF Online Editor'
    metadata['producer'] = 'Adobe Photoshop CC (Windows)'
    metadata['creationDate'] = 'D:20260501120000Z'
    metadata['modDate'] = 'D:20260606190000Z'  # ModDate is much later
    img_doc.set_metadata(metadata)
    
    img_doc.save(output_pdf)
    img_doc.close()
    doc.close()
    
    # Clean up temp files
    if os.path.exists(temp_jpeg):
        os.remove(temp_jpeg)
    if os.path.exists("temp_tampered_90.jpg"):
        os.remove("temp_tampered_90.jpg")
        
    print("Tampered PDF generated successfully.")

if __name__ == "__main__":
    os.makedirs("samples", exist_ok=True)
    clean_path = "samples/clean_salary_slip.pdf"
    tampered_path = "samples/tampered_salary_slip.pdf"
    
    generate_clean_pdf(clean_path)
    generate_tampered_pdf(clean_path, tampered_path)
    print("Done! Both PDFs are in the samples/ folder.")
