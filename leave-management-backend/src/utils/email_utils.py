from flask_mail import Message
from flask import current_app
from src.extensions import mail  # Importing from extensions avoids circular imports

def send_leave_notification(to_email, applicant_name, leave_type, start_date, end_date):
    try:
        subject = f"Leave Application Submitted by {applicant_name}"
        body = (
            f"{applicant_name} has applied for {leave_type} from "
            f"{start_date} to {end_date}.\nPlease log in to review."
        )

        msg = Message(subject=subject, recipients=[to_email], body=body)
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Email sending failed: {str(e)}")


def send_leave_status_update(to_email, applicant_name, status, comments=None):
    try:
        subject = f"Leave Application {status.capitalize()}"
        body = (
            f"Hello {applicant_name},\n\n"
            f"Your leave application has been {status}.\n\n"
            f"Comments: {comments if comments else 'No additional comments.'}\n\n"
            f"Regards,\nLeave Management System"
        )

        msg = Message(subject=subject, recipients=[to_email], body=body)
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Status update email failed: {str(e)}")
