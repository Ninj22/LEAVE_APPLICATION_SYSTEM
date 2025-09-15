from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date, timedelta, timezone
from sqlalchemy import and_, or_
from src.models.user import User
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
@jwt_required()
def get_leave_types():
    """Get all active leave types"""
    try:
        leave_types = LeaveType.query.filter_by(is_active=True).all()
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
        
        # Use user_id to match your models (not applicant_id)
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
    """Get user's leave balances"""
    try:
        current_user_id = get_jwt_identity()
        year = request.args.get('year', default=datetime.now().year, type=int)
        
        balances = LeaveBalance.query.filter_by(
            user_id=current_user_id, 
            year=year
        ).all()
        
        return jsonify({
            'balances': [balance.to_dict() for balance in balances]
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
def apply_for_leave():
    """Apply for leave"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['leave_type_id', 'start_date', 'end_date', 'reason']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Parse dates
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        # Calculate days
        days_requested = (end_date - start_date).days + 1
        
        # Create leave application - use user_id to match your User model
        application = LeaveApplication(
            user_id=current_user_id,  # Use user_id, not applicant_id
            leave_type_id=data['leave_type_id'],
            start_date=start_date,
            end_date=end_date,
            days_requested=days_requested,
            reason=data['reason']
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'message': 'Leave application submitted successfully',
            'application': application.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500