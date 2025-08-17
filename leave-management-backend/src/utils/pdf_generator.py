from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os
import tempfile

def generate_leave_application_pdf(application):
    """
    Generate PDF for a leave application
    Returns the path to the generated PDF file
    """
    try:
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        pdf_filename = f"leave_application_{application.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        
        # Header
        story.append(Paragraph("MINISTRY OF INFORMATION, COMMUNICATIONS AND THE DIGITAL ECONOMY", title_style))
        story.append(Paragraph("STATE DEPARTMENT FOR ICT AND DIGITAL ECONOMY", header_style))
        story.append(Spacer(1, 12))
        
        story.append(Paragraph("LEAVE APPLICATION FORM FOR MEMBERS OF STAFF UNDER H.O.DS", header_style))
        story.append(Spacer(1, 20))
        
        # Address section
        story.append(Paragraph("The Principal Secretary", normal_style))
        story.append(Paragraph("State Department for ICT & Digital Economy", normal_style))
        story.append(Paragraph("P.O.BOX 30025", normal_style))
        story.append(Paragraph("NAIROBI,", normal_style))
        story.append(Spacer(1, 20))
        
        # Application title
        story.append(Paragraph("APPLICATION FOR ANNUAL LEAVE", header_style))
        story.append(Paragraph("(To be submitted at least 30 days before the leave is due to begin)", normal_style))
        story.append(Spacer(1, 20))
        
        # PART 1 - Applicant section
        story.append(Paragraph("<b>PART 1</b>", header_style))
        story.append(Paragraph("(To be completed by the applicant)", normal_style))
        story.append(Spacer(1, 12))
        
        # Application details table
        application_data = [
            ['NAME:', application.applicant.full_name if application.applicant else 'N/A'],
            ['EMPLOYEE NUMBER:', application.applicant.employee_number if application.applicant else 'N/A'],
            ['', ''],
            ['Leave Type:', application.leave_type.name if application.leave_type else 'N/A'],
            ['Days Requested:', str(application.days_requested)],
            ['Start Date:', application.start_date.strftime('%d/%m/%Y') if application.start_date else 'N/A'],
            ['End Date:', application.end_date.strftime('%d/%m/%Y') if application.end_date else 'N/A'],
            ['', ''],
        ]
        
        if application.last_leave_from and application.last_leave_to:
            application_data.append(['Last Leave Period:', 
                                   f"{application.last_leave_from.strftime('%d/%m/%Y')} to {application.last_leave_to.strftime('%d/%m/%Y')}"])
        
        # Add contact information
        if application.contact_info:
            application_data.append(['Contact Info:', application.contact_info])
        
        # Add salary payment preference
        salary_pref = "Continue to be paid into bank account"
        if application.salary_payment_preference == "address" and application.salary_payment_address:
            salary_pref = f"Pay to address: {application.salary_payment_address}"
        application_data.append(['Salary Payment:', salary_pref])
        
        # Add person handling duties
        if application.person_handling_duties:
            application_data.append(['Person Handling Duties:', application.person_handling_duties.full_name])
        
        # Add permission note
        if application.permission_note_country:
            application_data.append(['Country Travel Note:', application.permission_note_country])
        
        application_data.extend([
            ['', ''],
            ['Application Date:', application.created_at.strftime('%d/%m/%Y') if application.created_at else 'N/A'],
            ['Applicant Signature:', application.applicant.full_name if application.applicant else 'N/A']
        ])
        
        # Create table
        app_table = Table(application_data, colWidths=[2*inch, 4*inch])
        app_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        story.append(app_table)
        story.append(Spacer(1, 30))
        
        # PART 2 - Approval section
        story.append(Paragraph("<b>PART 2</b>", header_style))
        story.append(Paragraph("(To be completed by the Principal Secretary)", normal_style))
        story.append(Spacer(1, 12))
        
        # Approval details
        approval_status = "Approved" if application.status == "approved" else "Not Approved"
        
        approval_data = [
            ['Status:', approval_status],
            ['', ''],
        ]
        
        # Add HOD approval details if available
        if application.hod_approved:
            approval_data.extend([
                ['HOD Approval Date:', application.hod_approval_date.strftime('%d/%m/%Y') if application.hod_approval_date else 'N/A'],
                ['HOD Comments:', application.hod_comments or 'None'],
                ['', ''],
            ])
        
        # Add Principal Secretary approval details if available
        if application.principal_secretary_approved:
            approval_data.extend([
                ['PS Approval Date:', application.principal_secretary_approval_date.strftime('%d/%m/%Y') if application.principal_secretary_approval_date else 'N/A'],
                ['PS Comments:', application.principal_secretary_comments or 'None'],
                ['PS Signature:', 'PRINCIPAL SECRETARY'],
            ])
        
        approval_table = Table(approval_data, colWidths=[2*inch, 4*inch])
        approval_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        story.append(approval_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"Generated on {datetime.now().strftime('%d/%m/%Y at %H:%M')}"
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph(footer_text, footer_style))
        
        # Build PDF
        doc.build(story)
        
        return pdf_path
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None

def generate_leave_summary_report(applications, title="Leave Applications Report"):
    """
    Generate a summary report of multiple leave applications
    """
    try:
        # Create temporary file
        temp_dir = tempfile.gettempdir()
        pdf_filename = f"leave_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.black,
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%d/%m/%Y at %H:%M')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        if not applications:
            story.append(Paragraph("No applications found.", styles['Normal']))
        else:
            # Create summary table
            table_data = [
                ['Employee', 'Leave Type', 'Start Date', 'End Date', 'Days', 'Status']
            ]
            
            for app in applications:
                table_data.append([
                    app.applicant.full_name if app.applicant else 'N/A',
                    app.leave_type.name if app.leave_type else 'N/A',
                    app.start_date.strftime('%d/%m/%Y') if app.start_date else 'N/A',
                    app.end_date.strftime('%d/%m/%Y') if app.end_date else 'N/A',
                    str(app.days_requested),
                    app.status.title()
                ])
            
            table = Table(table_data, colWidths=[1.2*inch, 1*inch, 0.8*inch, 0.8*inch, 0.5*inch, 0.7*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        # Build PDF
        doc.build(story)
        
        return pdf_path
        
    except Exception as e:
        print(f"Error generating summary report: {e}")
        return None
