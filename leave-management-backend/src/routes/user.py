from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'phone_number' in data:
            user.phone_number = data['phone_number']
        if 'email' in data:
            # Check if email is already taken by another user
            existing_user = User.query.filter(
                User.email == data['email'],
                User.id != user_id
            ).first()
            if existing_user:
                return jsonify({'error': 'Email already taken'}), 400
            user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@user_bp.route('/available-for-handover', methods=['GET'])
@jwt_required()
def get_available_for_handover():
    try:
        user_id = get_jwt_identity()
        
        # Get query parameters for date range
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not start_date_str or not end_date_str:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Get all users except the current user
        all_users = User.query.filter(User.id != user_id).all()
        
        # Find users who are on approved leave during the specified period
        from src.models.leave import LeaveApplication
        from sqlalchemy import and_, or_
        
        unavailable_user_ids = db.session.query(LeaveApplication.user_id).filter(
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
        
        # Sort by availability (available first) then by name
        users_data.sort(key=lambda x: (not x['available'], x['first_name'], x['last_name']))
        
        return jsonify({'users': users_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/all', methods=['GET'])
@jwt_required()
def get_all_users():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Only HODs and Principal Secretary can view all users
        if user.role not in ['hod', 'principal_secretary']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

