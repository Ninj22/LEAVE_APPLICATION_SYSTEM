from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func

from src.models.user import db, User
from src.models.leave import LeaveType, LeaveRequest, LeaveBalance

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        current_year = datetime.now().year
        
        # Common stats for all users
        stats = {
            'user': user.to_dict(),
            'current_year': current_year
        }
        
        # Leave balances
        balances = LeaveBalance.query.filter_by(
            user_id=user_id,
            year=current_year
        ).all()
        stats['leave_balances'] = [balance.to_dict() for balance in balances]
        
        # User's applications this year
        user_applications = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == user_id,
                db.extract('year', LeaveRequest.start_date) == current_year
            )
        ).all()
        
        stats['applications_this_year'] = len(user_applications)
        stats['pending_applications'] = len([app for app in user_applications if app.status == 'pending'])
        stats['approved_applications'] = len([app for app in user_applications if app.status == 'approved'])
        
        # Current leave status
        today = date.today()
        current_leave = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == user_id,
                LeaveRequest.status == 'approved',
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today
            )
        ).first()
        
        stats['currently_on_leave'] = current_leave.to_dict() if current_leave else None
        
        # Upcoming approved leaves
        upcoming_leaves = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == user_id,
                LeaveRequest.status == 'approved',
                LeaveRequest.start_date > today
            )
        ).order_by(LeaveRequest.start_date).limit(3).all()
        
        stats['upcoming_leaves'] = [leave.to_dict() for leave in upcoming_leaves]
        
        # Role-specific stats
        if user.role in ['hod', 'principal_secretary']:
            # Pending applications to review
            if user.role == 'hod':
                pending_to_review = LeaveRequest.query.join(User).filter(
                    and_(
                        LeaveRequest.status == 'pending',
                        User.role == 'staff'
                    )
                ).count()
            else:  # principal_secretary
                pending_to_review = LeaveRequest.query.join(User).filter(
                    and_(
                        LeaveRequest.status == 'pending',
                        User.role == 'hod'
                    )
                ).count()
            
            stats['pending_to_review'] = pending_to_review
            
            # Applications reviewed this month
            start_of_month = date.today().replace(day=1)
            reviewed_this_month = LeaveRequest.query.filter(
                and_(
                    LeaveRequest.approved_by == user_id,
                    LeaveRequest.approval_date >= start_of_month
                )
            ).count()
            
            stats['reviewed_this_month'] = reviewed_this_month
        
        if user.role == 'principal_secretary':
            # Additional stats for Principal Secretary
            total_staff = User.query.filter_by(role='staff').count()
            total_hods = User.query.filter_by(role='hod').count()
            
            stats['total_staff'] = total_staff
            stats['total_hods'] = total_hods
            
            # Staff currently on leave
            staff_on_leave = LeaveRequest.query.join(User).filter(
                and_(
                    User.role == 'staff',
                    LeaveRequest.status == 'approved',
                    LeaveRequest.start_date <= today,
                    LeaveRequest.end_date >= today
                )
            ).count()
            
            stats['staff_currently_on_leave'] = staff_on_leave
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/available-staff', methods=['GET'])
@jwt_required()
def get_available_staff():
    staff = User.query.filter_by(role='staff', available=True).all()
    return jsonify([u.to_dict() for u in staff]), 200

@dashboard_bp.route('/available-hods', methods=['GET'])
@jwt_required()
def get_available_hods():
    hods = User.query.filter_by(role='hod', available=True).all()
    return jsonify([u.to_dict() for u in hods]), 200

@dashboard_bp.route('/calendar', methods=['GET'])
@jwt_required()
def get_calendar_data():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters
        year = request.args.get('year', default=datetime.now().year, type=int)
        month = request.args.get('month', default=datetime.now().month, type=int)
        
        # Get user's approved leaves for the specified month/year
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        leaves = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == user_id,
                LeaveRequest.status == 'approved',
                or_(
                    and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= start_date),
                    and_(LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= end_date),
                    and_(LeaveRequest.start_date >= start_date, LeaveRequest.end_date <= end_date)
                )
            )
        ).all()
        
        # Format calendar data
        calendar_data = {
            'year': year,
            'month': month,
            'leaves': []
        }
        
        for leave in leaves:
            # Calculate actual leave days within the requested month
            leave_start = max(leave.start_date, start_date)
            leave_end = min(leave.end_date, end_date)
            
            leave_data = leave.to_dict()
            leave_data['calendar_start'] = leave_start.isoformat()
            leave_data['calendar_end'] = leave_end.isoformat()
            
            calendar_data['leaves'].append(leave_data)
        
        return jsonify(calendar_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/countdown', methods=['GET'])
@jwt_required()
def get_leave_countdown():
    try:
        user_id = get_jwt_identity()
        today = date.today()
        
        # Find the next upcoming approved leave
        next_leave = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == user_id,
                LeaveRequest.status == 'approved',
                LeaveRequest.start_date > today
            )
        ).order_by(LeaveRequest.start_date).first()
        
        if not next_leave:
            return jsonify({'countdown': None}), 200
        
        # Calculate countdown
        days_until = (next_leave.start_date - today).days
        
        # If leave starts today or is ongoing
        current_leave = LeaveRequest.query.filter(
            and_(
                LeaveRequest.employee_id == user_id,
                LeaveRequest.status == 'approved',
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today
            )
        ).first()
        
        if current_leave:
            days_remaining = (current_leave.end_date - today).days
            countdown_data = {
                'type': 'current_leave',
                'leave': current_leave.to_dict(),
                'days_remaining': days_remaining,
                'end_date': current_leave.end_date.isoformat()
            }
        else:
            countdown_data = {
                'type': 'upcoming_leave',
                'leave': next_leave.to_dict(),
                'days_until': days_until,
                'start_date': next_leave.start_date.isoformat()
            }
        
        return jsonify({'countdown': countdown_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/available-users', methods=['GET'])
@jwt_required()
def get_available_users():
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
        unavailable_user_ids = db.session.query(LeaveRequest.employee_id).filter(
            and_(
                LeaveRequest.status == 'approved',
                or_(
                    and_(LeaveRequest.start_date <= start_date, LeaveRequest.end_date >= start_date),
                    and_(LeaveRequest.start_date <= end_date, LeaveRequest.end_date >= end_date),
                    and_(LeaveRequest.start_date >= start_date, LeaveRequest.end_date <= end_date)
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
