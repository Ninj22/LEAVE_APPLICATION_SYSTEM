from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime

def generate_leave_application_pdf(application_data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom style for bold text
    styles.add(ParagraphStyle(name='BoldParagraph', parent=styles['Normal'], fontName='Helvetica-Bold'))

    story = []

    # Header
    story.append(Paragraph("MINISTRY OF INFORMATION, COMMUNICATIONS AND THE DIGITAL ECONOMY", styles['BoldParagraph']))
    story.append(Paragraph("STATE DEPARTMENT FOR ICT AND DIGITAL ECONOMY", styles['BoldParagraph']))
    story.append(Paragraph("LEAVE APPLICATION FORM FOR MEMBERS OF STAFF UNDER H.O.DS", styles['BoldParagraph']))
    story.append(Spacer(0, 0.2 * inch))

    story.append(Paragraph("The Principal Secretary", styles['Normal']))
    story.append(Paragraph("State Department for ICT & Digital Economy", styles['Normal']))
    story.append(Paragraph("P.O.BOX 30025", styles['Normal']))
    story.append(Paragraph("NAIROBI,", styles['Normal']))
    story.append(Spacer(0, 0.1 * inch))
    story.append(Paragraph("Through", styles['Normal']))
    story.append(Spacer(0, 0.2 * inch))

    # Leave Type
    story.append(Paragraph(f"<b>{application_data['leave_type_name'].upper()} APPLICATION FOR ANNUAL LEAVE</b>", styles['Normal']))
    story.append(Paragraph("(To be submitted at least 30 days before the leave is due to begin)", styles['Normal']))
    story.append(Spacer(0, 0.2 * inch))

    story.append(Paragraph("<b>PART 1</b>", styles['Normal']))
    story.append(Paragraph("(To be completed by the applicant)", styles['Normal']))
    story.append(Spacer(0, 0.1 * inch))

    # Applicant Details
    story.append(Paragraph(f"I hereby apply for <b>{application_data['days_requested']}</b> days annual leave beginning on <b>{application_data['start_date']}</b>, to <b>{application_data['end_date']}</b>.", styles['Normal']))
    story.append(Paragraph(f"The last leave taken by me was from <b>{application_data['last_leave_from'] if application_data['last_leave_from'] else 'N/A'}</b> to <b>{application_data['last_leave_to'] if application_data['last_leave_to'] else 'N/A'}</b>.", styles['Normal']))
    story.append(Paragraph(f"Total leave days balance to date is <b>{application_data['leave_balance']}</b>.", styles['Normal']))
    story.append(Spacer(0, 0.1 * inch))

    story.append(Paragraph("2. While on leave, my contact will be", styles['Normal']))
    story.append(Paragraph(f"<b>{application_data['contact_info']}</b>", styles['Normal']))
    story.append(Spacer(0, 0.1 * inch))

    story.append(Paragraph("3. During the period of my leave salary should", styles['Normal']))
    if application_data['salary_payment_preference'] == 'bank_account':
        story.append(Paragraph("a) <b>Continue to be paid into my bank account</b>", styles['Normal']))
        story.append(Paragraph("b) Be paid at the following address....................", styles['Normal']))
    else:
        story.append(Paragraph("a) Continue to be paid into my bank account", styles['Normal']))
        story.append(Paragraph(f"b) <b>Be paid at the following address: {application_data['salary_payment_address']}</b>", styles['Normal']))
    story.append(Spacer(0, 0.1 * inch))

    story.append(Paragraph("4. I understand that I will require permission should I desire to spend leave outside Kenya in accordance to Human Resource policies and Procedures Manual 2016.", styles['Normal']))
    story.append(Spacer(0, 0.1 * inch))

    story.append(Paragraph("5. While on leave <b>....................................................................</b> will handle duties of my office.", styles['Normal']))
    if application_data['person_handling_duties_name']:
        story.append(Paragraph(f"<b>{application_data['person_handling_duties_name']}</b> will handle duties of my office.", styles['Normal']))
    else:
        story.append(Paragraph("N/A", styles['Normal']))
    story.append(Spacer(0, 0.2 * inch))

    story.append(Paragraph(f"Date <b>{application_data['created_at']}</b>. Signature <b>{application_data['applicant_name']}</b>", styles['Normal']))
    story.append(Spacer(0, 0.4 * inch))

    # Principal Secretary Approval
    story.append(Paragraph("<b>(To be completed by the Principal Secretary)</b>", styles['Normal']))
    story.append(Paragraph(f"Approved/Not approved/ comments: <b>{application_data['principal_secretary_comments'] if application_data['principal_secretary_comments'] else 'N/A'}</b>", styles['Normal']))
    story.append(Paragraph(f"Date <b>{application_data['principal_secretary_approval_date'] if application_data['principal_secretary_approval_date'] else 'N/A'}</b>. Signed <b>PRINCIPAL SECRETARY</b>", styles['Normal']))
    story.append(Spacer(0, 0.2 * inch))

    doc.build(story)
