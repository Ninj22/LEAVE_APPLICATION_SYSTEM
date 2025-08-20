from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.extensions import db
from src.models.department import Department
from src.models.user import User

department_bp = Blueprint('department', __name__)

@department_bp.route('/', methods=['GET'])
@jwt_required()
def get_departments():
    """Get all departments"""
    try:
        departments = Department.query.all()
        return jsonify({
            'departments': [dept.to_dict() for dept in departments]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@department_bp.route('/<int:department_id>', methods=['GET'])
@jwt_required()
def get_department(department_id):
    """Get a specific department"""
    try:
        department = Department.query.get_or_404(department_id)
        return jsonify(department.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@department_bp.route('/', methods=['POST'])
@jwt_required()
def create_department():
    """Create a new department"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Check if user has permission (only admin or principal_secretary)
        if current_user.role not in ['admin', 'principal_secretary']:
            return jsonify({'error': 'Insufficient permissions'}), 403
            
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Department name is required'}), 400
            
        # Check if department already exists
        existing_dept = Department.query.filter_by(name=data['name']).first()
        if existing_dept:
            return jsonify({'error': 'Department already exists'}), 400
            
        # Create new department
        department = Department(
            name=data['name'],
            description=data.get('description', ''),
            hod_id=data.get('hod_id')
        )
        
        db.session.add(department)
        db.session.commit()
        
        return jsonify({
            'message': 'Department created successfully',
            'department': department.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@department_bp.route('/<int:department_id>', methods=['PUT'])
@jwt_required()
def update_department(department_id):
    """Update a department"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if current_user.role not in ['admin', 'principal_secretary']:
            return jsonify({'error': 'Insufficient permissions'}), 403
            
        department = Department.query.get_or_404(department_id)
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            # Check if new name already exists
            existing_dept = Department.query.filter(
                Department.name == data['name'],
                Department.id != department_id
            ).first()
            if existing_dept:
                return jsonify({'error': 'Department name already exists'}), 400
            department.name = data['name']
            
        if 'description' in data:
            department.description = data['description']
            
        if 'hod_id' in data:
            # Validate HOD exists and is eligible
            if data['hod_id']:
                hod = User.query.get(data['hod_id'])
                if not hod:
                    return jsonify({'error': 'Head of Department not found'}), 400
                if hod.role not in ['hod', 'admin']:
                    return jsonify({'error': 'User is not eligible to be HOD'}), 400
            department.hod_id = data['hod_id']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Department updated successfully',
            'department': department.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@department_bp.route('/<int:department_id>', methods=['DELETE'])
@jwt_required()
def delete_department(department_id):
    """Delete a department"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if current_user.role not in ['admin', 'principal_secretary']:
            return jsonify({'error': 'Insufficient permissions'}), 403
            
        department = Department.query.get_or_404(department_id)
        
        # Check if department has users
        users_in_dept = User.query.filter_by(department_id=department_id).count()
        if users_in_dept > 0:
            return jsonify({
                'error': 'Cannot delete department with assigned users. Please reassign users first.'
            }), 400
        
        db.session.delete(department)
        db.session.commit()
        
        return jsonify({'message': 'Department deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@department_bp.route('/<int:department_id>/users', methods=['GET'])
@jwt_required()
def get_department_users(department_id):
    """Get all users in a department"""
    try:
        department = Department.query.get_or_404(department_id)
        users = User.query.filter_by(department_id=department_id).all()
        
        return jsonify({
            'department': department.to_dict(),
            'users': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@department_bp.route('/<int:department_id>/assign-user', methods=['POST'])
@jwt_required()
def assign_user_to_department(department_id):
    """Assign a user to a department"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if current_user.role not in ['admin', 'principal_secretary', 'hod']:
            return jsonify({'error': 'Insufficient permissions'}), 403
            
        department = Department.query.get_or_404(department_id)
        data = request.get_json()
        
        if not data.get('user_id'):
            return jsonify({'error': 'User ID is required'}), 400
            
        user = User.query.get_or_404(data['user_id'])
        
        # If current user is HOD, they can only assign users to their own department
        if current_user.role == 'hod' and current_user.managed_department.id != department_id:
            return jsonify({'error': 'HOD can only assign users to their own department'}), 403
        
        user.department_id = department_id
        db.session.commit()
        
        return jsonify({
            'message': 'User assigned to department successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@department_bp.route('/user/<int:user_id>/remove', methods=['POST'])
@jwt_required()
def remove_user_from_department(user_id):
    """Remove a user from their department"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if current_user.role not in ['admin', 'principal_secretary', 'hod']:
            return jsonify({'error': 'Insufficient permissions'}), 403
            
        user = User.query.get_or_404(user_id)
        
        # If current user is HOD, they can only remove users from their own department
        if current_user.role == 'hod' and user.department_id != current_user.managed_department.id:
            return jsonify({'error': 'HOD can only remove users from their own department'}), 403
        
        user.department_id = None
        db.session.commit()
        
        return jsonify({
            'message': 'User removed from department successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@department_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_department_stats():
    """Get department statistics"""
    try:
        departments = Department.query.all()
        stats = []
        
        for dept in departments:
            user_count = User.query.filter_by(department_id=dept.id).count()
            active_users = User.query.filter_by(department_id=dept.id, is_active=True).count()
            
            stats.append({
                'department_id': dept.id,
                'department_name': dept.name,
                'total_users': user_count,
                'active_users': active_users,
                'hod_name': f"{dept.hod.first_name} {dept.hod.last_name}" if dept.hod else None
            })
        
        return jsonify({'department_stats': stats}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500