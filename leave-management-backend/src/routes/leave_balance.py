from flask import Blueprint, request, jsonify
from src.models.leave_balance import LeaveBalance
from src.models.user import User
from src.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity

leave_balance_bp = Blueprint('leave_balance', __name__)

@leave_balance_bp.route('/leave_balances', methods=['GET'])
@jwt_required()
def get_leave_balances():
    leave_balances = LeaveBalance.query.all()
    result = [{
        "user_id": lb.user_id,
        "annual_leave": lb.annual_leave,
        "sick_leave": lb.sick_leave,
        "maternity_leave": lb.maternity_leave,
        "paternity_leave": lb.paternity_leave,
        "compassionate_leave": lb.compassionate_leave,
        "study_leave": lb.study_leave
    } for lb in leave_balances]
    return jsonify(result), 200

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
