from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail, Message
from datetime import datetime, timedelta, timezone
import secrets
import re
from src.extensions import db
from src.models.user import User
from src.models.password_reset_token import PasswordResetToken
from src.models.leave_type import LeaveType
from src.models.leave_balance import LeaveBalance
import random
import string

auth_bp = Blueprint('auth', __name__)

def validate_employee_number(employee_number):
    """Validate employee number format and determine role"""
    if not employee_number or not employee_number.isdigit():
        return False, None
    
    length = len(employee_number)
    employee_num = int(employee_number)

    if length == 4 and 0 <= int(employee_number) <= 9999:
        return True, 'staff'
    elif length == 5 and 0 <= int(employee_number) <= 99999:
        return True, 'hod'
    elif length == 6 and 0 <= int(employee_number) <= 999999:
        return True, 'principal_secretary'
    
    return False, None

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    # Accept Kenyan phone numbers
    pattern = r'^(\+254|254|0)[17]\d{8}$'
    return re.match(pattern, phone) is not None

def generate_employee_number(role):
    """Generate unique employee number based on role"""
    if role == 'staff':
        length = 4
        min_val, max_val = 0, 9999
    elif role == 'hod':
        length = 5
        min_val, max_val = 0, 99999
    elif role == 'principal_secretary':
        length = 6
        min_val, max_val = 0, 999999
    else:
        return None
    
    max_attempts = 100
    for _ in range(max_attempts):
        employee_number = str(random.randint(min_val, max_val)).zfill(length)
        if not User.query.filter_by(employee_number=employee_number).first():
            return employee_number
    return None


@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        # Validate required fields
        required_fields = ['employee_number', 'email', 'phone_number', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
            
           # Validate role
        valid_roles = ['staff', 'hod', 'principal_secretary']
        if data['role'] not in valid_roles:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        if not validate_phone(data['phone_number']):
            return jsonify({'error': 'Invalid phone number format. Use (+254XXXXXXXXX)'}), 400
        
        #Check if user already exists
        if User.query.filter_by(employee_number=data['employee_number']).first():
            return jsonify({'error': 'Employee number already registered'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        if User.query.filter_by(phone_number=data['phone_number']).first():
            return jsonify({'error': 'Phone number already registered'}), 400
        
        #Generate employee number
        employee_number = generate_employee_number(data['role'])
        if not employee_number:
            return jsonify({'error': 'Failed to generate employee number. Try again.'}), 500
        
        user = User(
            employee_number=data['employee_number'],
            email=data['email'],
            phone_number=data['phone_number'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role= data['role'],
            is_active=False
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()

         # Initialize leave balances
        user.init_leave_balances()
        db.session.commit()
        
        token = user.generate_verification_token()
        user.email_verification_token = token
        db.session.commit()

        return jsonify({
            'message': 'User registered successfully',
            'employee_number': employee_number,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/signup-with-employee-number', methods=['POST'])
def signup_with_employee_number():
    """Register a new user with provided employee number"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['employee_number', 'email', 'phone_number', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate employee number and determine role
        is_valid, role = validate_employee_number(data['employee_number'])
        if not is_valid:
            return jsonify({'error': 'Invalid employee number format'}), 400
        
        # Validate email
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate phone
        if not validate_phone(data['phone_number']):
            return jsonify({'error': 'Invalid phone number format'}), 400
        
        # Check if user already exists
        if User.query.filter_by(employee_number=data['employee_number']).first():
            return jsonify({'error': 'Employee number already registered'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Create new user
        user = User(
            employee_number=data['employee_number'],
            email=data['email'],
            phone_number=data['phone_number'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=role
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Initialize leave balances
        user.init_leave_balances()
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user with employee number and password"""
    try:
        data = request.get_json()
        
        if not data.get('employee_number') or not data.get('password'):
            return jsonify({'error': 'Employee number and password are required'}), 400
        
        user = User.query.filter_by(employee_number=data['employee_number']).first()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if account is locked
        if user.is_locked:
            return jsonify({'error': 'Failed, kindly contact admin.'}), 423
        
        # Check password
        if not user.check_password(data['password']):
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 3:
                user.is_locked = True
                db.session.commit()
                return jsonify({'error': 'Failed, kindly contact admin.'}), 423
            
            db.session.commit()
            attempts_left = 3 - user.failed_login_attempts
            return jsonify({
                'error': f'Invalid credentials. {attempts_left} attempts remaining.'
            }), 401
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            additional_claims={
                'role': user.role,
                'employee_number': user.employee_number
            }
        )
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict(),
            'message': f'Welcome back, {user.first_name}!'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset token to user's phone/email"""
    try:
        data = request.get_json()
        
        identifier = data.get('email') or data.get('phone_number') or data.get('employee_number')
        if not identifier:
            return jsonify({'error': 'Email, phone number, or employee number is required'}), 400
        
        # Find user by email, phone, or employee number
        user = None
        if '@' in identifier:
            user = User.query.filter_by(email=identifier).first()
        elif identifier.isdigit():
            if len(identifier) <= 6:
                user = User.query.filter_by(employee_number=identifier).first()
            else:
                user = User.query.filter_by(phone_number=identifier).first()
        
        if not user:
            # Don't reveal if user exists or not
            return jsonify({'message': 'If the account exists, a reset code has been sent'}), 200
        
        # Generate 6-digit reset code
        reset_code = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        # Clean up old tokens
        PasswordResetToken.query.filter_by(user_id=user.id).delete()
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=reset_code,
            expires_at=expires_at
        )
        db.session.add(reset_token)
        db.session.commit()
        
        # In a real application, send SMS or email here
        # For now, we'll just return success (in development, you might return the code)
        response_data = {'message': 'Reset code has been sent to your registered phone number'}
        
        # Only include code in development
        if current_app.config.get('DEVELOPMENT', False):
            response_data['reset_code'] = reset_code  # Remove this in production
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/verify-reset-code', methods=['POST'])
def verify_reset_code():
    """Verify the reset code without changing password"""
    try:
        data = request.get_json()
        
        required_fields = ['code', 'identifier']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Find user
        identifier = data['identifier']
        user = None
        if '@' in identifier:
            user = User.query.filter_by(email=identifier).first()
        elif identifier.isdigit():
            if len(identifier) <= 6:
                user = User.query.filter_by(employee_number=identifier).first()
            else:
                user = User.query.filter_by(phone_number=identifier).first()
        
        if not user:
            return jsonify({'error': 'Invalid code'}), 400
        
        # Find valid token
        reset_token = PasswordResetToken.query.filter_by(
            user_id=user.id,
            token=data['code'],
            used=False
        ).first()
        
        if not reset_token or reset_token.expires_at < datetime.now(timezone.utc):
            return jsonify({'error': 'Invalid or expired code'}), 400
        
        return jsonify({
            'message': 'Code verified successfully',
            'user_id': user.id,
            'can_reset_password': True
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Reset password using verification code"""
    try:
        data = request.get_json()
        
        required_fields = ['code', 'identifier', 'new_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Find user
        identifier = data['identifier']
        user = None
        if '@' in identifier:
            user = User.query.filter_by(email=identifier).first()
        elif identifier.isdigit():
            if len(identifier) <= 6:
                user = User.query.filter_by(employee_number=identifier).first()
            else:
                user = User.query.filter_by(phone_number=identifier).first()
        
        if not user:
            return jsonify({'error': 'Invalid code'}), 400
        
        # Find valid token
        reset_token = PasswordResetToken.query.filter_by(
            user_id=user.id,
            token=data['code'],
            used=False
        ).first()
        
        if not reset_token or reset_token.expires_at < datetime.now(timezone.utc):
            return jsonify({'error': 'Invalid or expired code'}), 400
        
        # Validate password strength
        if len(data['new_password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Update password
        user.set_password(data['new_password'])
        user.failed_login_attempts = 0
        user.is_locked = False
        
        # Mark token as used
        reset_token.used = True
        
        db.session.commit()
        
        return jsonify({'message': 'Password reset successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/profile', methods=['GET'])
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

@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        # Verify current password
        if not user.check_password(data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        if len(data['new_password']) < 6:
            return jsonify({'error': 'New password must be at least 6 characters long'}), 400
        
        if data['current_password'] == data['new_password']:
            return jsonify({'error': 'New password must be different from current password'}), 400
        
        # Update password
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user"""
    # In this case, we don't need to do anything specific for logout
    # since JWT tokens are stateless and do not require server-side session management.
    # JWT tokens are stateless, so we just return success
    # In a production app, you might want to blacklist the token
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/unlock-account', methods=['POST'])
def unlock_account():
    """Unlock a locked account (admin only or with reset code)"""
    try:
        data = request.get_json()
        
        employee_number = data.get('employee_number')
        if not employee_number:
            return jsonify({'error': 'Employee number is required'}), 400
        
        user = User.query.filter_by(employee_number=employee_number).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.is_locked:
            return jsonify({'message': 'Account is not locked'}), 200
        
        # For now, allow unlocking with just employee number
        # In production, you might want admin authentication or reset code
        user.is_locked = False
        user.failed_login_attempts = 0
        db.session.commit()
        
        return jsonify({'message': 'Account unlocked successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    