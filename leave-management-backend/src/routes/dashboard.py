# src/routes/dashboard.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func, extract
from src.models.user import User
from src.models.leave_type import LeaveType
from src.models.leave_balance import LeaveBalance
from src.models.leave_application import LeaveApplication
from src.models.notification import Notification
from src.extensions import db
import calendar

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/types', methods=['GET'])
@jwt_required()
def get_leave_types():
    """Get all active leave types"""
    try:
        leave_types = LeaveType.query.filter_by(is_active=True).all()
        return jsonify({
            'leave_types': [lt.to_dict() for lt in leave_types]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# @dashboard_bp.route('/history', methods=['GET'])

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get comprehensive dashboard statistics for the user"""
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({'error': 'User not authenticated'}), 401
        
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        current_year = datetime.now().year
        today = date.today()
        
        # Base stats for all users
        stats = {
            'user': user.to_dict(),
            'current_year': current_year,
            'today': today.isoformat()
        }
        
        # Leave balances
        balances = LeaveBalance.get_user_all_balances(current_user_id, current_year)
        if not balances:
            # Initialize balances if they don't exist
            user.init_leave_balances()
            db.session.commit()
            balances = LeaveBalance.get_user_all_balances(current_user_id, current_year)
        
        stats['leave_balances'] = [balance.to_dict() for balance in balances]
        
        # Total leave balance summary
        total_allocated = sum(b.total_days for b in balances)
        total_used = sum(b.used_days for b in balances)
        total_remaining = sum(b.remaining_days() for b in balances)
        
        stats['leave_summary'] = {
            'total_allocated': total_allocated,
            'total_used': total_used,
            'total_remaining': total_remaining
        }
        
        # User's applications this year
        user_applications = LeaveApplication.query.filter(
            and_(
                LeaveApplication.applicant_id == current_user_id,
                extract('year', LeaveApplication.start_date) == current_year
            )
        ).all()
        
        stats['applications_this_year'] = len(user_applications)
        stats['applications_by_status'] = {
            'pending': len([app for app in user_applications if 'pending' in app.status]),
            'approved': len([app for app in user_applications if app.status == 'approved']),
            'rejected': len([app for app in user_applications if app.status == 'rejected']),
            'cancelled': len([app for app in user_applications if app.status == 'cancelled'])
        }
        
        # Current leave status
        current_leave = LeaveApplication.query.filter(
            and_(
                LeaveApplication.applicant_id == current_user_id,
                LeaveApplication.status == 'approved',
                LeaveApplication.start_date <= today,
                LeaveApplication.end_date >= today
            )
        ).first()
        
        if current_leave:
            days_remaining = (current_leave.end_date - today).days
            stats['current_leave'] = {
                'application': current_leave.to_dict(),
                'days_remaining': days_remaining,
                'is_on_leave': True
            }
        else:
            stats['current_leave'] = {'is_on_leave': False}
        
        # Upcoming approved leaves
        upcoming_leaves = LeaveApplication.query.filter(
            and_(
                LeaveApplication.applicant_id == current_user_id,
                LeaveApplication.status == 'approved',
                LeaveApplication.start_date > today
            )
        ).order_by(LeaveApplication.start_date).limit(5).all()
        
        stats['upcoming_leaves'] = [leave.to_dict() for leave in upcoming_leaves]
        
        # Next leave countdown
        if upcoming_leaves:
            next_leave = upcoming_leaves[0]
            days_until = (next_leave.start_date - today).days
            stats['next_leave_countdown'] = {
                'application': next_leave.to_dict(),
                'days_until': days_until
            }
        else:
            stats['next_leave_countdown'] = None
        
        # Notifications
        unread_notifications = Notification.get_unread_count(current_user_id)
        stats['unread_notifications'] = unread_notifications
        
        # Role-specific stats
        if user.role in ['hod', 'principal_secretary']:
            # Pending applications to review
            pending_query = LeaveApplication.query.join(User, LeaveApplication.applicant_id == User.id)
            
            if user.role == 'hod':
                pending_to_review = pending_query.filter(
                    and_(
                        LeaveApplication.status == 'pending_hod_approval',
                        User.role == 'staff'
                    )
                ).count()
            else:  # principal_secretary
                pending_to_review = pending_query.filter(
                    LeaveApplication.status == 'pending_principal_secretary_approval'
                ).count()
            
            stats['pending_to_review'] = pending_to_review
            
            # Applications reviewed this month
            start_of_month = today.replace(day=1)
            reviewed_query = LeaveApplication.query.filter(
                LeaveApplication.status.in_(['approved', 'rejected'])
            )
            
            if user.role == 'hod':
                reviewed_this_month = reviewed_query.filter(
                    and_(
                        LeaveApplication.hod_approval_date >= start_of_month,
                        LeaveApplication.hod_approval_date <= today
                    )
                ).count()
            else:
                reviewed_this_month = reviewed_query.filter(
                    and_(
                        LeaveApplication.principal_secretary_approval_date >= start_of_month,
                        LeaveApplication.principal_secretary_approval_date <= today
                    )
                ).count()
            
            stats['reviewed_this_month'] = reviewed_this_month
        
        # Principal Secretary specific stats
        if user.role == 'principal_secretary':
            total_staff = User.query.filter_by(role='staff').count()
            total_hods = User.query.filter_by(role='hod').count()
            
            stats['organization_stats'] = {
                'total_staff': total_staff,
                'total_hods': total_hods,
                'total_users': total_staff + total_hods + 1  # +1 for PS
            }
            
            # Staff currently on leave
            staff_on_leave = LeaveApplication.query.join(User).filter(
                and_(
                    User.role.in_(['staff', 'hod']),
                    LeaveApplication.status == 'approved',
                    LeaveApplication.start_date <= today,
                    LeaveApplication.end_date >= today
                )
            ).count()
            
            stats['staff_currently_on_leave'] = staff_on_leave
            
            # Leave applications this month
            applications_this_month = LeaveApplication.query.filter(
                extract('year', LeaveApplication.created_at) == today.year,
                extract('month', LeaveApplication.created_at) == today.month
            ).count()
            
            stats['applications_this_month'] = applications_this_month
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/calendar', methods=['GET'])
@jwt_required()
def get_calendar_data():
    """Get calendar data showing leave periods"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get query parameters
        year = request.args.get('year', default=datetime.now().year, type=int)
        month = request.args.get('month', default=datetime.now().month, type=int)
        view = request.args.get('view', default='personal')  # 'personal' or 'team'
        
        # Validate month and year
        if not (1 <= month <= 12):
            return jsonify({'error': 'Invalid month'}), 400
        
        # Calculate date range for the month
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Base query for leave applications
        leaves_query = LeaveApplication.query.filter(
            and_(
                LeaveApplication.status == 'approved',
                or_(
                    # Leave starts before month but ends in month
                    and_(LeaveApplication.start_date < start_date, LeaveApplication.end_date >= start_date),
                    # Leave starts in month but ends after month
                    and_(LeaveApplication.start_date <= end_date, LeaveApplication.end_date > end_date),
                    # Leave is entirely within month
                    and_(LeaveApplication.start_date >= start_date, LeaveApplication.end_date <= end_date)
                )
            )
        )
        
        # Filter based on view type and user role
        if view == 'personal':
            leaves_query = leaves_query.filter(LeaveApplication.applicant_id == user_id)
        elif view == 'team' and user.role in ['hod', 'principal_secretary']:
            # HODs see their staff, PS sees everyone
            if user.role == 'hod':
                # For now, show all staff - in a real system you'd filter by department
                leaves_query = leaves_query.join(User).filter(User.role == 'staff')
            # PS sees all by default (no additional filter needed)
        else:
            # Regular staff can only see personal view
            leaves_query = leaves_query.filter(LeaveApplication.applicant_id == user_id)
        
        leaves = leaves_query.all()
        
        # Process calendar data
        calendar_events = []
        for leave in leaves:
            # Calculate the actual dates that fall within the requested month
            event_start = max(leave.start_date, start_date)
            event_end = min(leave.end_date, end_date)
            
            event_data = {
                'id': leave.id,
                'title': f"{leave.applicant.first_name} - {leave.leave_type.name}",
                'applicant_name': leave.applicant.full_name,
                'leave_type': leave.leave_type.name,
                'start_date': event_start.isoformat(),
                'end_date': event_end.isoformat(),
                'full_start_date': leave.start_date.isoformat(),
                'full_end_date': leave.end_date.isoformat(),
                'days_requested': leave.days_requested,
                'status': leave.status,
                'is_current_user': leave.applicant_id == user_id
            }
            
            # Add different colors based on leave type
            leave_type_colors = {
                'Annual Leave': '#4CAF50',
                'Sick Leave': '#FF9800',
                'Maternity Leave': '#E91E63',
                'Paternity Leave': '#2196F3',
                'Bereavement Leave': '#424242',
                'Study Leave (Short Term)': '#9C27B0',
                'Study Leave (Long Term)': '#673AB7'
            }
            
            event_data['color'] = leave_type_colors.get(leave.leave_type.name, '#607D8B')
            calendar_events.append(event_data)
        
        # Generate month calendar structure
        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]
        
        calendar_data = {
            'year': year,
            'month': month,
            'month_name': month_name,
            'calendar_weeks': cal,
            'events': calendar_events,
            'view': view,
            'can_view_team': user.role in ['hod', 'principal_secretary'],
            'total_events': len(calendar_events)
        }
        
        return jsonify(calendar_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/countdown', methods=['GET'])
@jwt_required()
def get_leave_countdown():
    """Get countdown information for current or upcoming leave"""
    try:
        user_id = get_jwt_identity()
        today = date.today()
        
        # Check if user is currently on leave
        current_leave = LeaveApplication.query.filter(
            and_(
                LeaveApplication.applicant_id == user_id,
                LeaveApplication.status == 'approved',
                LeaveApplication.start_date <= today,
                LeaveApplication.end_date >= today
            )
        ).first()
        
        if current_leave:
            # Calculate remaining days
            days_remaining = (current_leave.end_date - today).days
            hours_remaining = days_remaining * 24
            
            # Calculate more precise time remaining
            now = datetime.now()
            end_datetime = datetime.combine(current_leave.end_date, datetime.min.time())
            time_diff = end_datetime - now
            
            countdown_data = {
                'type': 'current_leave',
                'status': 'on_leave',
                'leave': current_leave.to_dict(),
                'days_remaining': days_remaining,
                'hours_remaining': int(time_diff.total_seconds() // 3600),
                'minutes_remaining': int((time_diff.total_seconds() % 3600) // 60),
                'seconds_remaining': int(time_diff.total_seconds() % 60),
                'end_date': current_leave.end_date.isoformat(),
                'progress_percentage': ((current_leave.end_date - current_leave.start_date).days - days_remaining) / (current_leave.end_date - current_leave.start_date).days * 100
            }
            
            return jsonify({'countdown': countdown_data}), 200
        
        # Find next upcoming approved leave
        next_leave = LeaveApplication.query.filter(
            and_(
                LeaveApplication.applicant_id == user_id,
                LeaveApplication.status == 'approved',
                LeaveApplication.start_date > today
            )
        ).order_by(LeaveApplication.start_date).first()
        
        if next_leave:
            # Calculate time until leave starts
            days_until = (next_leave.start_date - today).days
            
            # Calculate more precise time until
            now = datetime.now()
            start_datetime = datetime.combine(next_leave.start_date, datetime.min.time())
            time_diff = start_datetime - now
            
            countdown_data = {
                'type': 'upcoming_leave',
                'status': 'waiting',
                'leave': next_leave.to_dict(),
                'days_until': days_until,
                'hours_until': int(time_diff.total_seconds() // 3600),
                'minutes_until': int((time_diff.total_seconds() % 3600) // 60),
                'seconds_until': int(time_diff.total_seconds() % 60),
                'start_date': next_leave.start_date.isoformat(),
                'end_date': next_leave.end_date.isoformat()
            }
            
            return jsonify({'countdown': countdown_data}), 200
        
        # No current or upcoming leave
        return jsonify({'countdown': None}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/balance-status', methods=['GET'])
@jwt_required()
def get_balance_status():
    """Get leave balance status with warnings"""
    try:
        user_id = get_jwt_identity()
        current_year = datetime.now().year
        
        balances = LeaveBalance.get_user_all_balances(user_id, current_year)
        balance_status = []
        
        for balance in balances:
            remaining = balance.remaining_days()
            percentage_used = (balance.used_days / balance.total_days) * 100 if balance.total_days > 0 else 0
            
            # Determine status
            if remaining <= 0:
                status = 'exhausted'
                warning = 'Leave balance exhausted'
            elif remaining <= 5:
                status = 'critical'
                warning = f'Only {remaining} days remaining'
            elif percentage_used >= 80:
                status = 'warning'
                warning = f'{percentage_used:.1f}% of leave used'
            else:
                status = 'good'
                warning = None
            
            balance_data = balance.to_dict()
            balance_data.update({
                'status': status,
                'warning': warning,
                'percentage_used': percentage_used,
                'percentage_remaining': 100 - percentage_used
            })
            
            balance_status.append(balance_data)
        
        return jsonify({'balance_status': balance_status}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/recent-activity', methods=['GET'])
@jwt_required()
def get_recent_activity():
    """Get recent leave-related activity"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        limit = request.args.get('limit', default=10, type=int)
        
        activities = []
        
        # User's recent applications
        recent_applications = LeaveApplication.query.filter_by(
            applicant_id=user_id
        ).order_by(LeaveApplication.created_at.desc()).limit(5).all()
        
        for app in recent_applications:
            activities.append({
                'type': 'application',
                'action': 'submitted',
                'description': f'Applied for {app.leave_type.name}',
                'date': app.created_at.isoformat(),
                'status': app.status,
                'application_id': app.id
            })
        
        # If user is HOD or PS, show recent approvals
        if user.role in ['hod', 'principal_secretary']:
            approval_field = 'hod_approval_date' if user.role == 'hod' else 'principal_secretary_approval_date'
            
            recent_approvals = LeaveApplication.query.filter(
                getattr(LeaveApplication, approval_field).isnot(None)
            ).order_by(getattr(LeaveApplication, approval_field).desc()).limit(5).all()
            
            for app in recent_approvals:
                approval_date = getattr(app, approval_field)
                activities.append({
                    'type': 'approval',
                    'action': 'approved' if app.status == 'approved' else 'processed',
                    'description': f'Processed {app.applicant.full_name}\'s {app.leave_type.name} application',
                    'date': approval_date.isoformat(),
                    'status': app.status,
                    'application_id': app.id
                })
        
        # Sort activities by date
        activities.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({'activities': activities[:limit]}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/team-overview', methods=['GET'])
@jwt_required()
def get_team_overview():
    """Get team leave overview (for HODs and PS only)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role not in ['hod', 'principal_secretary']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        today = date.today()
        
        # Get team members based on role
        if user.role == 'hod':
            # For now, get all staff - in real system you'd filter by department
            team_members = User.query.filter_by(role='staff').all()
        else:  # principal_secretary
            team_members = User.query.filter(User.role.in_(['staff', 'hod'])).all()
        
        team_overview = []
        
        for member in team_members:
            # Check if member is currently on leave
            current_leave = LeaveApplication.query.filter(
                and_(
                    LeaveApplication.applicant_id == member.id,
                    LeaveApplication.status == 'approved',
                    LeaveApplication.start_date <= today,
                    LeaveApplication.end_date >= today
                )
            ).first()
            
            # Get upcoming leave
            upcoming_leave = LeaveApplication.query.filter(
                and_(
                    LeaveApplication.applicant_id == member.id,
                    LeaveApplication.status == 'approved',
                    LeaveApplication.start_date > today
                )
            ).order_by(LeaveApplication.start_date).first()
            
            # Get leave balance summary
            current_year = datetime.now().year
            balances = LeaveBalance.get_user_all_balances(member.id, current_year)
            total_remaining = sum(b.remaining_days() for b in balances)
            
            member_data = {
                'user': member.to_dict(),
                'is_on_leave': current_leave is not None,
                'current_leave': current_leave.to_dict() if current_leave else None,
                'upcoming_leave': upcoming_leave.to_dict() if upcoming_leave else None,
                'total_leave_remaining': total_remaining,
                'leave_balances': [b.to_dict() for b in balances]
            }
            
            team_overview.append(member_data)
        
        # Summary statistics
        total_team = len(team_members)
        currently_on_leave = sum(1 for m in team_overview if m['is_on_leave'])
        available_team = total_team - currently_on_leave
        
        summary = {
            'total_team_members': total_team,
            'currently_on_leave': currently_on_leave,
            'available_members': available_team,
            'availability_percentage': (available_team / total_team * 100) if total_team > 0 else 0
        }
        
        return jsonify({
            'team_overview': team_overview,
            'summary': summary
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
