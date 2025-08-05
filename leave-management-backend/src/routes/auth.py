from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mail import Message, Mail
from datetime import datetime, timedelta, timezone
import secrets
import re
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User
# from src.utils.email import send_verification_email

from src.extensions import db
from src.models.user import User
from src.models.password_reset_token import PasswordResetToken



auth_bp = Blueprint('auth', __name__)

def validate_employee_number(employee_number):
    """Validate employee number format and determine role"""
    if not employee_number or not employee_number.isdigit():
        return False, None
    
    length = len(employee_number)
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

def send_reset_email():
    data = request.get_json()
    email = data.get("email")
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    reset_token = secrets.token_urlsafe(16)
    # In a real app, store this token in DB with expiration

    mail = Mail(current_app)
    msg = Message("Password Reset", recipients=[email])
    msg.body = f"Click here to reset your password: http://yourdomain.com/reset/{reset_token}"
    mail.send(msg)

    return jsonify({"msg": "Reset email sent"}), 200

def register_user():
    """Register a new user"""
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "User already exists"}), 409

    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User registered"}), 201

def register():
    """Register a new user with email verification"""
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        email=data['email'],
        password=hashed_password,
        role=data['role'],
        is_active=False
    )
    db.session.add(new_user)
    db.session.commit()

    # Generate token + save
    token = new_user.generate_verification_token()
    new_user.verification_token = token
    db.session.commit()

    # Send email (example)
    # send_verification_email(new_user.email, token)

    return jsonify({"message": "Registration successful. Check email to verify."}), 201

def validate_phone(phone):
    """Validate phone number format"""
    pattern = r'^\+?[1-9]\d{1,14}$'
    return re.match(pattern, phone) is not None

@auth_bp.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['employee_number', 'email', 'phone_number', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate employee number
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
        
        # Initialize leave balances for the current year
        from src.models.leave import LeaveType, LeaveBalance
        current_year = datetime.now().year
        leave_types = LeaveType.query.all()
        
        for leave_type in leave_types:
            balance = LeaveBalance(
                user_id=user.id,
                leave_type_id=leave_type.id,
                balance_days=leave_type.max_days,
                year=current_year
            )
            db.session.add(balance)
        
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
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.is_active:
        return jsonify({"error": "Account not verified"}), 403
    try:
        data = request.get_json()
        
        if not data.get('employee_number') or not data.get('password'):
            return jsonify({'error': 'Employee number and password are required'}), 400
        
        user = User.query.filter_by(employee_number=data['employee_number']).first()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if account is locked
        if user.is_locked:
            return jsonify({'error': 'Account locked. Please contact admin.'}), 423
        
        # Check password
        if not user.check_password(data['password']):
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 3:
                user.is_locked = True
                db.session.commit()
                return jsonify({'error': 'Failed, kindly contact admin.'}), 423
            
            db.session.commit()
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def login_user():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        token = create_access_token(identity=email)
        return jsonify(access_token=token), 200

    return jsonify({"msg": "Invalid credentials"}), 401

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            # Don't reveal if email exists or not
            return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200
        
        # Generate reset token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.session.add(reset_token)
        db.session.commit()
        
        # Send email (if mail is configured)
        try:
            mail = Mail(current_app)
            msg = Message(
                'Password Reset Request',
                recipients=[user.email],
                body=f'''
Hello {user.first_name},

You have requested a password reset for your leave management account.

Your reset token is: {token}

This token will expire in 1 hour.

If you did not request this reset, please ignore this email.

Best regards,
Leave Management System
                '''
            )
            mail.send(msg)
        except Exception as mail_error:
            # Log the error but don't fail the request
            print(f"Failed to send email: {mail_error}")
        
        return jsonify({'message': 'If the email exists, a reset link has been sent'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json()
        
        required_fields = ['token', 'new_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Find valid token
        reset_token = PasswordResetToken.query.filter_by(
            token=data['token'],
            used=False
        ).first()
        
        if not reset_token or reset_token.expires_at < datetime.utcnow():
            return jsonify({'error': 'Invalid or expired token'}), 400
        
        # Update password
        user = User.query.get(reset_token.user_id)
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

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # JWT tokens are stateless, so we just return success
    # In a production app, you might want to blacklist the token
    return jsonify({'message': 'Logged out successfully'}), 200

