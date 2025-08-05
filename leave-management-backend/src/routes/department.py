from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User
from src.models.department import Department

department_bp = Blueprint("department", __name__)

@department_bp.route("/", methods=["POST"])
@jwt_required()
def create_department():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "principal_secretary":
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json()
        name = data.get("name")
        hod_id = data.get("hod_id")

        if not name:
            return jsonify({"error": "Department name is required"}), 400

        existing_department = Department.query.filter_by(name=name).first()
        if existing_department:
            return jsonify({"error": "Department with this name already exists"}), 400

        if hod_id:
            hod = User.query.get(hod_id)
            if not hod or hod.role != "hod":
                return jsonify({"error": "Invalid HOD ID or user is not an HOD"}), 400
            # Check if HOD is already assigned to another department
            if hod.department:
                return jsonify({"error": f"HOD {hod.first_name} {hod.last_name} is already assigned to {hod.department.name}"}), 400

        department = Department(name=name, hod_id=hod_id)
        db.session.add(department)
        db.session.commit()

        # Assign department to HOD if provided
        if hod_id:
            hod.department_id = department.id
            db.session.commit()

        return jsonify({"message": "Department created successfully", "department": department.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@department_bp.route("/", methods=["GET"])
@jwt_required()
def get_departments():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role not in ["principal_secretary", "hod"]:
            return jsonify({"error": "Unauthorized"}), 403

        departments = Department.query.all()
        return jsonify({"departments": [d.to_dict() for d in departments]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@department_bp.route("/<int:department_id>", methods=["PUT"])
@jwt_required()
def update_department(department_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "principal_secretary":
            return jsonify({"error": "Unauthorized"}), 403

        department = Department.query.get(department_id)
        if not department:
            return jsonify({"error": "Department not found"}), 404

        data = request.get_json()
        new_name = data.get("name")
        new_hod_id = data.get("hod_id")

        if new_name and new_name != department.name:
            existing_department = Department.query.filter_by(name=new_name).first()
            if existing_department:
                return jsonify({"error": "Department with this name already exists"}), 400
            department.name = new_name

        if new_hod_id is not None:
            if new_hod_id == department.hod_id:
                pass # No change
            elif new_hod_id == "": # Unassign HOD
                if department.hod:
                    department.hod.department_id = None
                department.hod_id = None
            else:
                new_hod = User.query.get(new_hod_id)
                if not new_hod or new_hod.role != "hod":
                    return jsonify({"error": "Invalid HOD ID or user is not an HOD"}), 400
                if new_hod.department and new_hod.department.id != department.id:
                    return jsonify({"error": f"HOD {new_hod.first_name} {new_hod.last_name} is already assigned to {new_hod.department.name}"}), 400
                
                # Unassign old HOD if exists
                if department.hod and department.hod.id != new_hod_id:
                    department.hod.department_id = None
                
                department.hod_id = new_hod_id
                new_hod.department_id = department.id

        db.session.commit()

        return jsonify({"message": "Department updated successfully", "department": department.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@department_bp.route("/<int:department_id>", methods=["DELETE"])
@jwt_required()
def delete_department(department_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "principal_secretary":
            return jsonify({"error": "Unauthorized"}), 403

        department = Department.query.get(department_id)
        if not department:
            return jsonify({"error": "Department not found"}), 404

        # Unassign HOD if exists
        if department.hod:
            department.hod.department_id = None

        db.session.delete(department)
        db.session.commit()

        return jsonify({"message": "Department deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@department_bp.route("/<int:department_id>/assign-hod", methods=["PUT"])
@jwt_required()
def assign_hod_to_department(department_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "principal_secretary":
            return jsonify({"error": "Unauthorized"}), 403

        department = Department.query.get(department_id)
        if not department:
            return jsonify({"error": "Department not found"}), 404

        data = request.get_json()
        hod_id = data.get("hod_id")

        if not hod_id:
            return jsonify({"error": "HOD ID is required"}), 400

        hod = User.query.get(hod_id)
        if not hod or hod.role != "hod":
            return jsonify({"error": "Invalid HOD ID or user is not an HOD"}), 400

        # Check if HOD is already assigned to another department
        if hod.department and hod.department.id != department_id:
            return jsonify({"error": f"HOD {hod.first_name} {hod.last_name} is already assigned to {hod.department.name}"}), 400

        # Unassign old HOD if exists
        if department.hod and department.hod.id != hod_id:
            department.hod.department_id = None

        department.hod_id = hod_id
        hod.department_id = department.id
        db.session.commit()

        return jsonify({"message": "HOD assigned successfully", "department": department.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@department_bp.route("/<int:department_id>/unassign-hod", methods=["PUT"])
@jwt_required()
def unassign_hod_from_department(department_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "principal_secretary":
            return jsonify({"error": "Unauthorized"}), 403

        department = Department.query.get(department_id)
        if not department:
            return jsonify({"error": "Department not found"}), 404

        if not department.hod_id:
            return jsonify({"message": "Department does not have an assigned HOD"}), 200

        hod = department.hod
        hod.department_id = None
        department.hod_id = None
        db.session.commit()

        return jsonify({"message": "HOD unassigned successfully", "department": department.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@department_bp.route("/<int:department_id>/assign-staff", methods=["PUT"])
@jwt_required()
def assign_staff_to_department(department_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "principal_secretary":
            return jsonify({"error": "Unauthorized"}), 403

        department = Department.query.get(department_id)
        if not department:
            return jsonify({"error": "Department not found"}), 404

        data = request.get_json()
        staff_ids = data.get("staff_ids")

        if not isinstance(staff_ids, list) or not staff_ids:
            return jsonify({"error": "List of staff_ids is required"}), 400

        for staff_id in staff_ids:
            staff = User.query.get(staff_id)
            if not staff or staff.role != "staff":
                return jsonify({"error": f"Invalid staff ID {staff_id} or user is not staff"}), 400
            staff.department_id = department.id
            db.session.add(staff)
        db.session.commit()

        return jsonify({"message": "Staff assigned to department successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@department_bp.route("/<int:department_id>/unassign-staff", methods=["PUT"])
@jwt_required()
def unassign_staff_from_department(department_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "principal_secretary":
            return jsonify({"error": "Unauthorized"}), 403

        department = Department.query.get(department_id)
        if not department:
            return jsonify({"error": "Department not found"}), 404

        data = request.get_json()
        staff_ids = data.get("staff_ids")

        if not isinstance(staff_ids, list) or not staff_ids:
            return jsonify({"error": "List of staff_ids is required"}), 400

        for staff_id in staff_ids:
            staff = User.query.get(staff_id)
            if not staff or staff.role != "staff" or staff.department_id != department_id:
                return jsonify({"error": f"Invalid staff ID {staff_id} or staff not in this department"}), 400
            staff.department_id = None
            db.session.add(staff)
        db.session.commit()

        return jsonify({"message": "Staff unassigned from department successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@department_bp.route("/staff-by-department/<int:department_id>", methods=["GET"])
@jwt_required()
def get_staff_by_department(department_id):
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role not in ["principal_secretary", "hod"]:
            return jsonify({"error": "Unauthorized"}), 403

        department = Department.query.get(department_id)
        if not department:
            return jsonify({"error": "Department not found"}), 404

        staff_members = User.query.filter_by(department_id=department_id, role="staff").all()
        return jsonify({"staff": [s.to_dict() for s in staff_members]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@department_bp.route("/hods-without-department", methods=["GET"])
@jwt_required()
def get_hods_without_department():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != "principal_secretary":
            return jsonify({"error": "Unauthorized"}), 403

        hods = User.query.filter(User.role == "hod", User.department_id == None).all()
        return jsonify({"hods": [h.to_dict() for h in hods]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500