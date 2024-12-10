from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from datetime import datetime
import os

def clean_unit_name(unit_text):
    """Clean and format the unit name"""
    if not unit_text:
        return ""
    
    prefixes = ["UNITE DE ", "Unité de ", "UNITÉ DE ", "Unite de "]
    cleaned_text = unit_text
    for prefix in prefixes:
        if cleaned_text.startswith(prefix):
            cleaned_text = cleaned_text[len(prefix):]
            break
    
    return cleaned_text.strip()

def create_paragraph_style(name, font_name='Helvetica', font_size=10, text_color=colors.black, 
                         alignment=0, space_before=0, space_after=0, leading=12):
    """Create a custom paragraph style"""
    return ParagraphStyle(
        name,
        fontName=font_name,
        fontSize=font_size,
        textColor=text_color,
        alignment=alignment,
        spaceBefore=space_before,
        spaceAfter=space_after,
        leading=leading,
        wordWrap='CJK'  # Improved word wrapping
    )

def create_incident_pdf(incidents, output_path, unit=None):
    """Generate a PDF report for incidents"""
    # Document setup
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    elements = []
    
    # Custom styles
    title_style = create_paragraph_style(
        'CustomTitle',
        font_name='Helvetica',
        font_size=14,
        alignment=0,  # Left alignment
        space_after=2
    )
    
    # Header with logo
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'ona_logoFull.png')
    
    # Create header content
    header_text = [
        [Paragraph("OFFICE NATIONAL DE L'ASSAINISSEMENT", title_style)],
        [Paragraph("ZONE D'ALGER", title_style)]
    ]
    
    if unit:
        cleaned_unit = clean_unit_name(unit)
        if cleaned_unit:
            header_text.append([Paragraph(f"UNITE DE {cleaned_unit.upper()}", title_style)])
    
    # Create header table with logo
    if os.path.exists(logo_path):
        img = Image(logo_path)
        img.drawHeight = 2.0 * inch
        img.drawWidth = 2.0 * inch
        
        header_table_data = [
            [
                Table(header_text, colWidths=[350]),
                img
            ]
        ]
        
        header_table = Table(header_table_data, colWidths=[400, 200])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(header_table)
    else:
        header_table = Table(header_text)
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(header_table)
    
    # Add title "Rapport des Incidents"
    title_style = create_paragraph_style(
        'ReportTitle',
        font_name='Helvetica-Bold',
        font_size=16,
        alignment=1,  # Center
        space_before=20,
        space_after=20
    )
    elements.append(Paragraph("Rapport des Incidents", title_style))
    
    # Add generation date
    date_style = create_paragraph_style('DateStyle', font_size=10, alignment=0)
    generation_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    elements.append(Paragraph(f"Généré le {generation_date}", date_style))
    elements.append(Spacer(1, 10))
    
    # Create cell styles for content
    cell_style = create_paragraph_style(
        'CellStyle',
        font_size=9,
        leading=12,
        alignment=4  # Justified alignment
    )
    
    # Table headers
    headers = [
        'Type de Station',
        'Wilaya',
        'Commune',
        'Localités',
        'Nature et Cause',
        'Date et Heure',
        'Mesures Prises',
        'Impact'
    ]
    
    # Convert headers to Paragraph objects
    header_style = create_paragraph_style(
        'HeaderStyle',
        font_name='Helvetica-Bold',
        font_size=10,
        alignment=1  # Center alignment
    )
    headers = [Paragraph(h, header_style) for h in headers]
    
    # Table data with proper text wrapping
    data = [headers]
    for incident in incidents:
        row = [
            Paragraph('Conduits', cell_style),
            Paragraph(incident.wilaya, cell_style),
            Paragraph(incident.commune, cell_style),
            Paragraph(incident.localite, cell_style),
            Paragraph(incident.nature_cause, cell_style),
            Paragraph(incident.date_incident.strftime('%Y-%m-%d\n%H:%M'), cell_style),
            Paragraph(incident.mesures_prises, cell_style),
            Paragraph(incident.impact, cell_style)
        ]
        data.append(row)
    
    # Column widths in millimeters (adjusted for better text display)
    col_widths = [25*mm, 20*mm, 25*mm, 25*mm, 35*mm, 25*mm, 35*mm, 35*mm]
    
    # Create table with row heights
    table = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Table style
    table_style = TableStyle([
        # Header style - using the exact color from the image
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8cb2e3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        
        # Alignment
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Font
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        
        # Minimum row height
        ('MINROWHEIGHT', (0, 0), (-1, -1), 40),
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
