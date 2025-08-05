from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import and_, or_
from datetime import datetime, date, timedelta, timezone
from src.models.user import db, User
from src.models.leave_type import LeaveType
from src.models.leave_balance import LeaveBalance
from src.models.leave_application import LeaveApplication  # If it exists
from src.utils.email_utils import send_leave_notification
from src.holidays import get_kenyan_public_holidays
from src.utils.email_utils import send_leave_status_update
from src.models.notification import Notification
from src.utils.pdf_generator import generate_leave_application_pdf
import os

leave_bp = Blueprint("leave", __name__)

def calculate_working_days(start_date, end_date, exclude_weekends=True):
    """Calculate working days between two dates, excluding weekends and public holidays"""
    working_days = 0
    current_date = start_date
    
    # Get public holidays for the year of the leave
    public_holidays = get_kenyan_public_holidays(start_date.year)

    while current_date <= end_date:
        # Monday = 0, Sunday = 6
        if exclude_weekends and current_date.weekday() >= 5:  # Saturday or Sunday
            current_date += timedelta(days=1)
            continue
        
        if current_date in public_holidays:
            current_date += timedelta(days=1)
            continue

        working_days += 1
        current_date += timedelta(days=1)
    
    return working_days

@leave_bp.route("types", methods=['GET'])
def get_leave_types():
    try:
        leave_types = LeaveType.query.all()
        return jsonify({
            "leave_types": [leave_type.to_dict() for leave_type in leave_types]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@leave_bp.route('/balances', methods=['GET'])
@jwt_required()
def get_leave_balances():
    try:
        user_id = get_jwt_identity()
        current_year = datetime.now(timezone.utc).year
        
        balances = LeaveBalance.query.filter_by(
            user_id=user_id,
            year=current_year
        ).all()
        
        return jsonify({
            "balances": [balance.to_dict() for balance in balances]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_leave():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        subject = data.get('subject')
        if subject and not isinstance(subject, str):
            return jsonify({'msg': 'Subject must be a string'}), 422
        
        # Validate required fields
        required_fields = ['leave_type_id', 'start_date', 'end_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Parse dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if start_date > end_date:
            return jsonify({'error': 'Start date must be before end date'}), 400
        
        if start_date < date.today():
            return jsonify({'error': 'Cannot apply for past dates'}), 400
        
        # Get leave type
        leave_type = LeaveType.query.get(data['leave_type_id'])
        if not leave_type:
            return jsonify({'error': 'Invalid leave type'}), 400
        
        # Calculate days requested
        days_requested = calculate_working_days(start_date, end_date, leave_type.exclude_weekends)
        
        # Check leave balance
        current_year = datetime.now(timezone.utc).year
        balance = LeaveBalance.query.filter_by(
            user_id=user_id,
            leave_type_id=data['leave_type_id'],
            year=current_year
        ).first()
        
        if not balance or balance.balance_days < days_requested:
            return jsonify({'error': 'Insufficient leave balance'}), 400
        
        # Check for overlapping applications
        overlapping = LeaveApplication.query.filter(
            and_(
                LeaveApplication.user_id == user_id,
                LeaveApplication.status.in_(['pending', 'approved']),
                or_(
                    and_(LeaveApplication.start_date <= start_date, LeaveApplication.end_date >= start_date),
                    and_(LeaveApplication.start_date <= end_date, LeaveApplication.end_date >= end_date),
                    and_(LeaveApplication.start_date >= start_date, LeaveApplication.end_date <= end_date)
                )
            )
        ).first()
        
        if overlapping:
            return jsonify({'error': 'You have overlapping leave applications'}), 400
        
        # Parse optional date fields
        last_leave_from = None
        last_leave_to = None
        if data.get('last_leave_from'):
            try:
                last_leave_from = datetime.strptime(data['last_leave_from'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid last_leave_from date format'}), 400
        
        if data.get('last_leave_to'):
            try:
                last_leave_to = datetime.strptime(data['last_leave_to'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid last_leave_to date format'}), 400
        
        # Validate person handling duties
        person_handling_duties_id = data.get('person_handling_duties_id')
        if person_handling_duties_id:
            person = User.query.get(person_handling_duties_id)
            if not person:
                return jsonify({'error': 'Invalid person for handling duties'}), 400
            
            # Check if person is available (not on approved leave during this period)
            person_leave = LeaveApplication.query.filter(
                and_(
                    LeaveApplication.user_id == person_handling_duties_id,
                    LeaveApplication.status == 'approved',
                    or_(
                        and_(LeaveApplication.start_date <= start_date, LeaveApplication.end_date >= start_date),
                        and_(LeaveApplication.start_date <= end_date, LeaveApplication.end_date >= end_date),
                        and_(LeaveApplication.start_date >= start_date, LeaveApplication.end_date <= end_date)
                    )
                )
            ).first()
            
            if person_leave:
                return jsonify({'error': 'Selected person is not available during your leave period'}), 400
        
        # Create leave application
        application = LeaveApplication(
            user_id=user_id,
            leave_type_id=data["leave_type_id"],
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            last_leave_from=last_leave_from,
            last_leave_to=last_leave_to,
            contact_info=data.get("contact_info"),
            salary_payment_preference=data.get("salary_payment_preference", "bank_account"),
            salary_payment_address=data.get("salary_payment_address"),
            permission_note_country=data.get("permission_note_country"),
            person_handling_duties_id=person_handling_duties_id,
            subject=subject
        )
        
         # Set initial status based on applicant role
        applicant = User.query.get(user_id)
        if applicant.role == "staff":
            application.status = "pending_hod_approval"
        elif applicant.role == "hod":
            application.status = "pending_principal_secretary_approval"
        else:
            application.status = "pending" # Default for other roles if any

        db.session.add(application)
        db.session.commit()

        # ✅ Now send email
        try:
            leave_type = LeaveType.query.get(application.leave_type_id)
            leave_type_name = leave_type.name if leave_type else "Unknown"

            send_leave_notification(
                to_email=applicant.email,  # replace with actual logic if needed
                applicant_name=applicant.full_name,
                leave_type=leave_type_name,
                start_date=application.start_date,
                end_date=application.end_date
            )
        except Exception as e:
            print("Email sending skipped:", e)

        return jsonify({
            'message': 'Leave application submitted successfully',
            'application': application.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@leave_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_user_applications():
    try:
        user_id = get_jwt_identity()
        
        applications = LeaveApplication.query.filter_by(user_id=user_id).order_by(
            LeaveApplication.created_at.desc()
        ).all()
        
        return jsonify({
            'applications': [app.to_dict() for app in applications]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_applications():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Only HODs and Principal Secretary can view  applications
        if user.role not in ['hod', 'principal_secretary']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # HODs see staff applications, Principal Secretary sees HOD applications
        if user.role == 'hod':
            # Get staff applications
            applications = LeaveApplication.query.join(User).filter(
                and_(
                    LeaveApplication.status == 'pending',
                    User.role == 'staff'
                )
            ).order_by(LeaveApplication.created_at.desc()).all()
        else:  # principal_secretary
            # Get HOD applications
            applications = LeaveApplication.query.join(User).filter(
                and_(
                    LeaveApplication.status == 'pending',
                    User.role == 'hod'
                )
            ).order_by(LeaveApplication.created_at.desc()).all()
        
        return jsonify({
            'applications': [app.to_dict() for app in applications]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/approve/<int:application_id>', methods=['PUT'])
@jwt_required()
def approve_reject_application(application_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        data = request.get_json()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        if user.role not in ['hod', 'principal_secretary']:
            return jsonify({'error': 'Unauthorized'}), 403

        application = LeaveApplication.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404

        if application.status not in ['pending_hod_approval', 'pending_principal_secretary_approval']:
            return jsonify({'error': 'Application already processed or not in a valid state'}), 400

        applicant = User.query.get(application.user_id)
        action = data.get('action')
        message = ""

        if user.role == 'hod':
            if applicant.role != 'staff':
                return jsonify({'error': 'HODs can only approve staff applications'}), 403
            if application.status != 'pending_hod_approval':
                return jsonify({'error': 'Application is not pending HOD approval'}), 400

            if action == 'approve':
                application.hod_approved = True
                application.hod_approval_date = datetime.now(timezone.utc)
                application.hod_comments = data.get('comments', '')
                application.status = 'pending_principal_secretary_approval'
                message = 'Application approved by HOD, pending Principal Secretary approval.'

            elif action == 'reject':
                application.status = 'rejected'
                application.hod_comments = data.get('comments', '')
                message = 'Application rejected by HOD.'

            else:
                return jsonify({'error': 'Invalid action'}), 400

        elif user.role == 'principal_secretary':
            if applicant.role not in ['staff', 'hod']:
                return jsonify({'error': 'Principal Secretary can only approve staff or HOD applications'}), 403
            if application.status != 'pending_principal_secretary_approval':
                return jsonify({'error': 'Application is not pending Principal Secretary approval'}), 400

            if action == 'approve':
                application.principal_secretary_approved = True
                application.principal_secretary_approval_date = datetime.now(timezone.utc)
                application.principal_secretary_comments = data.get('comments', '')
                application.status = 'approved'
                message = 'Application approved by Principal Secretary.'

                # Deduct leave balance after final approval
                current_year = datetime.now(timezone.utc).year
                balance = LeaveBalance.query.filter_by(
                    user_id=application.user_id,
                    leave_type_id=application.leave_type_id,
                    year=current_year
                ).first()
                if balance:
                    balance.balance_days -= application.days_requested

            # Generate PDF after final approval
                pdf_data = {
                    "leave_type_name": application.leave_type.name,
                    "days_requested": application.days_requested,
                    "start_date": application.start_date.strftime("%d.%m.%Y"),
                    "end_date": application.end_date.strftime("%d.%m.%Y"),
                    "last_leave_from": application.last_leave_from.strftime("%d.%m.%Y") if application.last_leave_from else None,
                    "last_leave_to": application.last_leave_to.strftime("%d.%m.%Y") if application.last_leave_to else None,
                    "leave_balance": balance.balance_days if balance else "N/A", # Use updated balance
                    "contact_info": application.contact_info,
                    "salary_payment_preference": application.salary_payment_preference,
                    "salary_payment_address": application.salary_payment_address,
                    "permission_note_country": application.permission_note_country,
                    "person_handling_duties_name": application.person_handling_duties.first_name + " " + application.person_handling_duties.last_name if application.person_handling_duties else "N/A",
                    "created_at": application.created_at.strftime("%d.%m.%Y"),
                    "applicant_name": application.applicant.first_name + " " + application.applicant.last_name,
                    "principal_secretary_comments": application.principal_secretary_comments,
                    "principal_secretary_approval_date": application.principal_secretary_approval_date.strftime("%d.%m.%Y") if application.principal_secretary_approval_date else None
                }
            else: # reject
                application.status = 'rejected'
                application.principal_secretary_comments = data.get('comments', '')
                message = 'Application rejected by Principal Secretary.'
        else:
            return jsonify({'error': 'Unauthorized to approve applications'}), 403

        db.session.commit()
        db.session.refresh(application)
        if application.leave_type: db.session.refresh(application.leave_type)
        if application.applicant: db.session.refresh(application.applicant)
        if application.person_handling_duties: db.session.refresh(application.person_handling_duties)

        return jsonify({
            'message': message,
            'application': application.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@leave_bp.route("/download_pdf/<int:application_id>", methods=["GET"])
@jwt_required()
def download_pdf(application_id):
    try:
        user_id = get_jwt_identity()
        application = LeaveApplication.query.get(application_id)

        if not application:
            return jsonify({"error": "Application not found"}), 404

        # Only the applicant or Principal Secretary can download the PDF
        if user_id != application.user_id and User.query.get(user_id).role != "principal_secretary":
            return jsonify({"error": "Unauthorized to download this PDF"}), 403

        if application.status != "approved":
            return jsonify({"error": "PDF is only available for approved leaves"}), 400

        pdf_path = f"/tmp/leave_application_{application_id}.pdf"
        if not os.path.exists(pdf_path):
            return jsonify({"error": "PDF not found. It might not have been generated yet."}), 404

        return send_file(pdf_path, as_attachment=True, download_name=f"leave_application_{application_id}.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@leave_bp.route("/generate_pdf/<int:application_id>", methods=["POST"])
@jwt_required()   
def generate_leave_application_pdf(application_id):
    try:
        user_id = get_jwt_identity()
        application = LeaveApplication.query.get(application_id)

        if not application:
            return jsonify({"error": "Application not found"}), 404

        # Only the applicant or Principal Secretary can generate the PDF
        if user_id != application.user_id and User.query.get(user_id).role != "principal_secretary":
            return jsonify({"error": "Unauthorized to generate this PDF"}), 403

        pdf_path = generate_leave_application_pdf(application)
        if not pdf_path:
            return jsonify({"error": "Failed to generate PDF"}), 500

        return send_file(pdf_path, as_attachment=True, download_name=f"leave_application_{application_id}.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@jwt_required()
def get_leave_history():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        status = request.args.get('status')
        year = request.args.get('year', type=int)
        
        query = LeaveApplication.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if year:
            query = query.filter(
                db.extract('year', LeaveApplication.start_date) == year
            )
        
        applications = query.order_by(LeaveApplication.created_at.desc()).all()
        
        return jsonify({
            'history': [app.to_dict() for app in applications]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


