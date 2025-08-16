from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import and_, or_
from src.models.user import db, User
from src.models.leave import LeaveType, LeaveRequest, LeaveBalance
from src.utils.email_utils import send_leave_notification, send_leave_status_update
from src.holidays import get_kenyan_public_holidays
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
        if exclude_weekends and current_date.weekday() >= 5:  # Saturday or Sunday
            current_date += timedelta(days=1)
            continue
        
        if current_date in public_holidays:
            current_date += timedelta(days=1)
            continue

        working_days += 1
        current_date += timedelta(days=1)
    
    return working_days

@leave_bp.route("/types", methods=['GET'])
def get_leave_types():
    try:
        leave_types = LeaveType.query.all()
        return jsonify({
            "leave_types": [leave_type.to_dict() for leave_type in leave_types]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        
        if not balance or balance.balance < days_requested:
            return jsonify({'error': 'Insufficient leave balance'}), 400
        
        # Check for overlapping applications
        overlapping = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == user_id,
                LeaveRequest.status.in_(['Pending', 'approved']),
                or_(
                    and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= start_date),
                    and_(LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= end_date),
                    and_(LeaveRequest.start_date >= start_date, LeaveRequest.end_date <= end_date)
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
            
            # Check if person is available
            person_leave = LeaveRequest.query.filter(
                and_(
                    LeaveRequest.employee_id == person_handling_duties_id,
                    LeaveRequest.status == 'approved',
                    or_(
                        and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= start_date),
                        and_(LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= end_date),
                        and_(LeaveRequest.start_date >= start_date, LeaveRequest.end_date <= end_date)
                    )
                )
            ).first()
            
            if person_leave:
                return jsonify({'error': 'Selected person is not available during your leave period'}), 400
        
        # Create leave request
        application = LeaveRequest(
            employee_id=user_id,
            leave_type_id=data["leave_type_id"],
            start_date=start_date,
            end_date=end_date,
            reason=subject,
            person_handling_duties_id=person_handling_duties_id
        )
        
        # Set initial status based on applicant role
        applicant = User.query.get(user_id)
        if applicant.role == "staff":
            application.status = "pending_hod_approval"
        elif applicant.role == "hod":
            application.status = "pending_principal_secretary_approval"
        else:
            application.status = "Pending"

        db.session.add(application)
        db.session.commit()

        # Send email notification
        try:
            leave_type_name = leave_type.name if leave_type else "Unknown"
            send_leave_notification(
                to_email=applicant.email,
                applicant_name=f"{applicant.first_name} {applicant.last_name}",
                leave_type=leave_type_name,
                start_date=application.start_date,
                end_date=application.end_date
            )
        except Exception as e:
            print(f"Email sending failed: {e}")

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
        
        applications = LeaveRequest.query.filter_by(employee_id=user_id).order_by(
            LeaveRequest.applied_on.desc()
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
        
        if user.role not in ['hod', 'principal_secretary']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        if user.role == 'hod':
            applications = LeaveRequest.query.join(User).filter(
                and_(
                    LeaveRequest.status == 'pending_hod_approval',
                    User.role == 'staff'
                )
            ).order_by(LeaveRequest.applied_on.desc()).all()
        else:  # principal_secretary
            applications = LeaveRequest.query.join(User).filter(
                and_(
                    LeaveRequest.status == 'pending_principal_secretary_approval',
                    User.role == 'hod'
                )
            ).order_by(LeaveRequest.applied_on.desc()).all()
        
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

        application = LeaveRequest.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404

        if application.status not in ['pending_hod_approval', 'pending_principal_secretary_approval']:
            return jsonify({'error': 'Application already processed or not in a valid state'}), 400

        applicant = User.query.get(application.employee_id)
        action = data.get('action')
        message = ""

        if user.role == 'hod':
            if applicant.role != 'staff':
                return jsonify({'error': 'HODs can only approve staff applications'}), 403
            if application.status != 'pending_hod_approval':
                return jsonify({'error': 'Application is not pending HOD approval'}), 400

            if action == 'approve':
                application.status = 'pending_principal_secretary_approval'
                application.approved_by = user_id
                application.approval_date = datetime.now(timezone.utc)
                message = 'Application approved by HOD, pending Principal Secretary approval.'

            elif action == 'reject':
                application.status = 'rejected'
                application.approved_by = user_id
                application.approval_date = datetime.now(timezone.utc)
                message = 'Application rejected by HOD.'

            else:
                return jsonify({'error': 'Invalid action'}), 400

        elif user.role == 'principal_secretary':
            if applicant.role not in ['staff', 'hod']:
                return jsonify({'error': 'Principal Secretary can only approve staff or HOD applications'}), 403
            if application.status != 'pending_principal_secretary_approval':
                return jsonify({'error': 'Application is not pending Principal Secretary approval'}), 400

            if action == 'approve':
                application.status = 'approved'
                application.approved_by = user_id
                application.approval_date = datetime.now(timezone.utc)
                message = 'Application approved by Principal Secretary.'

                # Deduct leave balance
                current_year = datetime.now(timezone.utc).year
                balance = LeaveBalance.query.filter_by(
                    user_id=application.employee_id,
                    leave_type_id=application.leave_type_id,
                    year=current_year
                ).first()
                if balance:
                    balance.balance -= calculate_working_days(
                        application.start_date, application.end_date, application.leave_type.exclude_weekends
                    )

            elif action == 'reject':
                application.status = 'rejected'
                application.approved_by = user_id
                application.approval_date = datetime.now(timezone.utc)
                message = 'Application rejected by Principal Secretary.'

            else:
                return jsonify({'error': 'Invalid action'}), 400

        db.session.commit()
        db.session.refresh(application)
        if application.leave_type: db.session.refresh(application.leave_type)
        if application.employee: db.session.refresh(application.employee)
        if application.person_handling_duties: db.session.refresh(application.person_handling_duties)

        # Send status update email
        try:
            send_leave_status_update(
                to_email=applicant.email,
                applicant_name=f"{applicant.first_name} {applicant.last_name}",
                leave_type=application.leave_type.name,
                status=application.status,
                comments=data.get('comments', '')
            )
        except Exception as e:
            print(f"Email sending failed: {e}")

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
        application = LeaveRequest.query.get(application_id)

        if not application:
            return jsonify({"error": "Application not found"}), 404

        if user_id != application.employee_id and User.query.get(user_id).role != "principal_secretary":
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
def generate_leave_application_pdf_route(application_id):
    try:
        user_id = get_jwt_identity()
        application = LeaveRequest.query.get(application_id)

        if not application:
            return jsonify({"error": "Application not found"}), 404

        if user_id != application.employee_id and User.query.get(user_id).role != "principal_secretary":
            return jsonify({"error": "Unauthorized to generate this PDF"}), 403

        pdf_path = generate_leave_application_pdf(application)
        if not pdf_path:
            return jsonify({"error": "Failed to generate PDF"}), 500

        return send_file(pdf_path, as_attachment=True, download_name=f"leave_application_{application_id}.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@leave_bp.route("/history", methods=['GET'])
@jwt_required()
def get_leave_history():
    try:
        user_id = get_jwt_identity()
        
        status = request.args.get('status')
        year = request.args.get('year', type=int)
        
        query = LeaveRequest.query.filter_by(employee_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if year:
            query = query.filter(
                db.extract('year', LeaveRequest.start_date) == year
            )
        
        applications = query.order_by(LeaveRequest.applied_on.desc()).all()
        
        return jsonify({
            'history': [app.to_dict() for app in applications]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

