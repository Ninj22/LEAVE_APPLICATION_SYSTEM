from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import and_, or_
from src.models.user import User
from src.models.leave import LeaveRequest
from src.models.leave_type import LeaveType
from src.models.leave_balance import LeaveBalance
from src.models.leave_application import LeaveApplication
from src.utils.email_utils import send_leave_notification, send_leave_status_update
from src.holidays import get_kenyan_public_holidays
from src.models.notification import Notification
from src.utils.pdf_generator import generate_leave_application_pdf
import os
from src.extensions import db

leave_bp = Blueprint("leave", __name__)

def calculate_working_days(start_date, end_date, exclude_weekends=True):
    """Calculate working days between two dates, excluding weekends and public holidays"""
    if start_date > end_date:
        return 0
        
    working_days = 0
    current_date = start_date
    
    # Get public holidays for the years involved
    years = set()
    temp_date = start_date
    while temp_date <= end_date:
        years.add(temp_date.year)
        temp_date = temp_date.replace(year=temp_date.year + 1) if temp_date.month == 12 and temp_date.day == 31 else temp_date + timedelta(days=365)
    
    public_holidays = set()
    for year in years:
        public_holidays.update(get_kenyan_public_holidays(year))

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

@leave_bp.route("/types", methods=['GET'])
def get_leave_types():
    try:
        leave_types = LeaveType.query.all()
        return jsonify({
            "leave_types": [leave_type.to_dict() for leave_type in leave_types]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@leave_bp.route('/history', methods=['GET'])
@jwt_required()
def get_leave_history():
    """Get user's leave history"""
    try:
        current_user_id = get_jwt_identity()
        year = request.args.get('year', type=int)
        
        query = LeaveApplication.query.filter_by(user_id=current_user_id)
        if year:
            query = query.filter(db.extract('year', LeaveApplication.start_date) == year)
            
        applications = query.order_by(LeaveApplication.created_at.desc()).all()
        
        return jsonify({
            'applications': [app.to_dict() for app in applications]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@leave_bp.route('/balances', methods=['GET'])
@jwt_required()
def get_leave_balances():
    """Get current user's leave balances"""
    try:
        user_id = get_jwt_identity()
        current_year = datetime.now().year
        
        balances = LeaveBalance.get_user_all_balances(user_id, current_year)
        
        # If no balances exist, create them
        if not balances:
            user = User.query.get(user_id)
            if user:
                user.init_leave_balances()
                db.session.commit()
                balances = LeaveBalance.get_user_all_balances(user_id, current_year)
        
        return jsonify({
            "balances": [balance.to_dict() for balance in balances]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@leave_bp.route('/balance/<int:leave_type_id>', methods=['GET'])
@jwt_required()
def get_leave_balance_by_type(leave_type_id):
    """Get user's balance for specific leave type"""
    try:
        user_id = get_jwt_identity()
        current_year = datetime.now().year
        
        balance = LeaveBalance.get_user_balance(user_id, leave_type_id, current_year)
        
        if not balance:
            return jsonify({'error': 'Leave balance not found'}), 404
        
        return jsonify({'balance': balance.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_applications():
    """Get pending leave applications for approval"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Only HOD and Principal Secretary can see pending applications
        if current_user.role not in ['hod', 'principal_secretary']:
            return jsonify({'error': 'Insufficient permissions'}), 403
            
        applications = LeaveApplication.query.filter_by(status='pending').all()
        
        return jsonify({
            'applications': [app.to_dict() for app in applications]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/apply', methods=['POST'])
@jwt_required()
def apply_leave():
    """Submit a new leave application"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        data = request.get_json()
        
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
            return jsonify({'error': 'Start date must be before or equal to end date'}), 400
        
        if start_date < date.today():
            return jsonify({'error': 'Cannot apply for past dates'}), 400
        
        # Get leave type
        leave_type = LeaveType.query.get(data['leave_type_id'])
        if not leave_type or not leave_type.is_active:
            return jsonify({'error': 'Invalid or inactive leave type'}), 400
        
        # Calculate days requested
        days_requested = calculate_working_days(start_date, end_date, leave_type.exclude_weekends)
        
        if days_requested <= 0:
            return jsonify({'error': 'Invalid date range - no working days selected'}), 400
        
        # Check leave balance
        current_year = datetime.now().year
        balance = LeaveBalance.get_user_balance(user_id, data['leave_type_id'], current_year)
        
        if not balance:
            return jsonify({'error': 'Leave balance not initialized'}), 400
        
        if not balance.can_take_leave(days_requested):
            return jsonify({
                'error': f'Insufficient leave balance. Requested: {days_requested} days, Available: {balance.remaining_days()} days'
            }), 400
        
        # Check for overlapping applications
        overlapping = LeaveApplication.query.filter(
            and_(
                LeaveApplication.applicant_id == user_id,
                LeaveApplication.status.in_(['pending', 'pending_hod_approval', 'pending_principal_secretary_approval', 'approved']),
                or_(
                    and_(LeaveApplication.start_date <= start_date, LeaveApplication.end_date >= start_date),
                    and_(LeaveApplication.start_date <= end_date, LeaveApplication.end_date >= end_date),
                    and_(LeaveApplication.start_date >= start_date, LeaveApplication.end_date <= end_date)
                )
            )
        ).first()
        
        if overlapping:
            return jsonify({'error': 'You have overlapping leave applications for this period'}), 400
        
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
            
            # Check if person is available during leave period
            person_leave = LeaveApplication.query.filter(
                and_(
                    LeaveApplication.applicant_id == person_handling_duties_id,
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
            applicant_id=user_id,
            leave_type_id=data["leave_type_id"],
            subject=data.get('subject'),
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            last_leave_from=last_leave_from,
            last_leave_to=last_leave_to,
            contact_info=data.get("contact_info"),
            salary_payment_preference=data.get("salary_payment_preference", "bank_account"),
            salary_payment_address=data.get("salary_payment_address"),
            permission_note_country=data.get("permission_note_country"),
            person_handling_duties_id=person_handling_duties_id
        )
        
        # Set initial status based on applicant role
        if user.role == "staff":
            application.status = "pending_hod_approval"
        elif user.role == "hod":
            application.status = "pending_principal_secretary_approval"
        else:
            application.status = "pending"

        db.session.add(application)
        db.session.commit()
        
        # Create notifications for approvers
        if user.role == "staff":
            # Notify all HODs
            hods = User.query.filter_by(role='hod').all()
            for hod in hods:
                Notification.create_leave_application_notification(hod.id, application)
        elif user.role == "hod":
            # Notify Principal Secretary
            ps_users = User.query.filter_by(role='principal_secretary').all()
            for ps in ps_users:
                Notification.create_leave_application_notification(ps.id, application)
        
        db.session.commit()

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
    """Get current user's leave applications"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        status = request.args.get('status')
        year = request.args.get('year', type=int)
        limit = request.args.get('limit', default=50, type=int)
        
        query = LeaveApplication.query.filter_by(applicant_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        if year:
            query = query.filter(
                db.extract('year', LeaveApplication.start_date) == year
            )
        
        applications = query.order_by(
            LeaveApplication.created_at.desc()
        ).limit(limit).all()
        
        return jsonify({
            'applications': [app.to_dict() for app in applications]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_applications():
    """Get applications pending approval by current user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Only HODs and Principal Secretary can view pending applications
        if user.role not in ['hod', 'principal_secretary']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        applications = []
        
        if user.role == 'hod':
            # Get staff applications pending HOD approval
            applications = LeaveApplication.query.join(User, LeaveApplication.applicant_id == User.id).filter(
                and_(
                    LeaveApplication.status == 'pending_hod_approval',
                    User.role == 'staff'
                )
            ).order_by(LeaveApplication.created_at.desc()).all()
            
        elif user.role == 'principal_secretary':
            # Get applications pending Principal Secretary approval
            applications = LeaveApplication.query.join(User, LeaveApplication.applicant_id == User.id).filter(
                LeaveApplication.status == 'pending_principal_secretary_approval'
            ).order_by(LeaveApplication.created_at.desc()).all()
        
        return jsonify({
            'applications': [app.to_dict() for app in applications]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/approve/<int:application_id>', methods=['PUT'])
@jwt_required()
def approve_reject_application(application_id):
    """Approve or reject a leave application"""
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

        action = data.get('action')  # 'approve' or 'reject'
        comments = data.get('comments', '')

        if action not in ['approve', 'reject']:
            return jsonify({'error': 'Invalid action. Use "approve" or "reject"'}), 400

        # Check if user can approve this application
        if not application.can_be_approved_by(user):
            return jsonify({'error': 'You cannot approve this application at this stage'}), 403

        if user.role == 'hod':
            if action == 'approve':
                application.hod_approved = True
                application.hod_approval_date = datetime.now(timezone.utc)
                application.hod_comments = comments
                application.status = 'pending_principal_secretary_approval'
                
                # Notify Principal Secretary
                ps_users = User.query.filter_by(role='principal_secretary').all()
                for ps in ps_users:
                    Notification.create_leave_application_notification(ps.id, application)
                
                # Notify applicant of HOD approval
                Notification.create_leave_approval_notification(application.applicant_id, application, user)
                
                message = 'Application approved by HOD, pending Principal Secretary approval.'
                
            else:  # reject
                application.status = 'rejected'
                application.hod_comments = comments
                
                # Notify applicant of rejection
                Notification.create_leave_rejection_notification(application.applicant_id, application, user, comments)
                
                message = 'Application rejected by HOD.'

        elif user.role == 'principal_secretary':
            if action == 'approve':
                application.principal_secretary_approved = True
                application.principal_secretary_approval_date = datetime.now(timezone.utc)
                application.principal_secretary_comments = comments
                application.status = 'approved'
                
                # Deduct leave balance after final approval
                current_year = datetime.now().year
                balance = LeaveBalance.get_user_balance(
                    application.applicant_id,
                    application.leave_type_id,
                    current_year
                )
                if balance:
                    balance.use_leave_days(application.days_requested)
                
                # Notify applicant of final approval
                Notification.create_leave_approval_notification(application.applicant_id, application, user)
                
                message = 'Application fully approved.'
                
            else:  # reject
                application.status = 'rejected'
                application.principal_secretary_comments = comments
                
                # Notify applicant of rejection
                Notification.create_leave_rejection_notification(application.applicant_id, application, user, comments)
                
                message = 'Application rejected by Principal Secretary.'

        db.session.commit()

        return jsonify({
            'message': message,
            'application': application.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/cancel/<int:application_id>', methods=['PUT'])
@jwt_required()
def cancel_application(application_id):
    """Cancel a pending leave application"""
    try:
        user_id = get_jwt_identity()
        application = LeaveApplication.query.get(application_id)

        if not application:
            return jsonify({'error': 'Application not found'}), 404

        # Only the applicant can cancel their own application
        if application.applicant_id != user_id:
            return jsonify({'error': 'You can only cancel your own applications'}), 403

        # Can only cancel pending applications
        if application.status not in ['pending', 'pending_hod_approval', 'pending_principal_secretary_approval']:
            return jsonify({'error': 'Cannot cancel processed applications'}), 400

        application.status = 'cancelled'
        db.session.commit()

        return jsonify({
            'message': 'Application cancelled successfully',
            'application': application.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_leave():
    """Get user's current active leave"""
    try:
        user_id = get_jwt_identity()
        today = date.today()
        
        current_leave = LeaveApplication.query.filter(
            and_(
                LeaveApplication.applicant_id == user_id,
                LeaveApplication.status == 'approved',
                LeaveApplication.start_date <= today,
                LeaveApplication.end_date >= today
            )
        ).first()
        
        if current_leave:
            return jsonify({
                'current_leave': current_leave.to_dict(),
                'days_remaining': (current_leave.end_date - today).days
            }), 200
        else:
            return jsonify({'current_leave': None}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/upcoming', methods=['GET'])
@jwt_required()
def get_upcoming_leaves():
    """Get user's upcoming approved leaves"""
    try:
        user_id = get_jwt_identity()
        today = date.today()
        
        upcoming_leaves = LeaveApplication.query.filter(
            and_(
                LeaveApplication.applicant_id == user_id,
                LeaveApplication.status == 'approved',
                LeaveApplication.start_date > today
            )
        ).order_by(LeaveApplication.start_date).all()
        
        return jsonify({
            'upcoming_leaves': [leave.to_dict() for leave in upcoming_leaves]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/available-users', methods=['GET'])
@jwt_required()
def get_available_users():
    """Get users available for duty handover during specified period"""
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters for date range
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Get all users except the current user
        all_users = User.query.filter(User.id != user_id).all()
        
        # Find users who are on approved leave during the specified period
        unavailable_user_ids = db.session.query(LeaveApplication.applicant_id).filter(
            and_(
                LeaveApplication.status == 'approved',
                or_(
                    and_(LeaveApplication.start_date <= start_date, LeaveApplication.end_date >= start_date),
                    and_(LeaveApplication.start_date <= end_date, LeaveApplication.end_date >= end_date),
                    and_(LeaveApplication.start_date >= start_date, LeaveApplication.end_date <= end_date)
                )
            )
        ).distinct().all()
        
        unavailable_ids = [uid[0] for uid in unavailable_user_ids]
        
        # Format user data with availability status
        users_data = []
        for user in all_users:
            user_dict = user.to_dict()
            user_dict['available'] = user.id not in unavailable_ids
            users_data.append(user_dict)
        
        return jsonify({'users': users_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@leave_bp.route('/generate-pdf/<int:application_id>', methods=['POST'])
@jwt_required()
def generate_pdf(application_id):
    """Generate PDF for approved leave application"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        application = LeaveApplication.query.get(application_id)

        if not application:
            return jsonify({"error": "Application not found"}), 404

        # Only the applicant or Principal Secretary can generate PDF
        if user_id != application.applicant_id and user.role != "principal_secretary":
            return jsonify({"error": "Unauthorized to generate this PDF"}), 403

        if application.status != "approved":
            return jsonify({"error": "PDF is only available for approved applications"}), 400

        # Generate PDF
        pdf_path = generate_leave_application_pdf(application)
        if not pdf_path or not os.path.exists(pdf_path):
            return jsonify({"error": "Failed to generate PDF"}), 500

        # Update application record
        application.pdf_generated = True
        application.pdf_path = pdf_path
        db.session.commit()

        return send_file(
            pdf_path, 
            as_attachment=True, 
            download_name=f"leave_application_{application_id}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@leave_bp.route('/download-pdf/<int:application_id>', methods=['GET'])
@jwt_required()
def download_pdf(application_id):
    """Download existing PDF for approved leave application"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        application = LeaveApplication.query.get(application_id)

        if not application:
            return jsonify({"error": "Application not found"}), 404

        # Only the applicant or Principal Secretary can download PDF
        if user_id != application.applicant_id and user.role != "principal_secretary":
            return jsonify({"error": "Unauthorized to download this PDF"}), 403

        if application.status != "approved":
            return jsonify({"error": "PDF is only available for approved applications"}), 400

        if not application.pdf_path or not os.path.exists(application.pdf_path):
            return jsonify({"error": "PDF not found. Generate it first."}), 404

        return send_file(
            application.pdf_path,
            as_attachment=True,
            download_name=f"leave_application_{application_id}.pdf",
            mimetype='application/pdf'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500