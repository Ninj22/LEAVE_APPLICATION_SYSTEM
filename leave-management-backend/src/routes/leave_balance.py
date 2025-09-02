from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.extensions import db
from src.models.leave_balance import LeaveBalance
from datetime import datetime, timezone

leave_balance_bp = Blueprint('leave_balance', __name__)

@leave_balance_bp.route('/leave_balances', methods=['GET'])
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

@leave_balance_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_leave_balance(user_id):
    lb = LeaveBalance.query.filter_by(user_id=user_id).first()
    if not lb:
        return jsonify({"error": "Leave balance not found"}), 404
    result = {
        "user_id": lb.user_id,
        "annual_leave": lb.annual_leave,
        "sick_leave": lb.sick_leave,
        "maternity_leave": lb.maternity_leave,
        "paternity_leave": lb.paternity_leave,
        "compassionate_leave": lb.compassionate_leave,
        "study_leave": lb.study_leave
    }
    return jsonify(result), 200
