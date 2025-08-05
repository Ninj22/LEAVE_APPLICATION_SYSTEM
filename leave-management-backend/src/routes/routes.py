from flask import Blueprint
from .auth import register_user, login_user, send_reset_email

# Define blueprints
main_bp = Blueprint("main", __name__)  # Only one "main"
notifications_bp = Blueprint("notifications", __name__)

# Auth routes
@main_bp.route("/register", methods=["POST"])
def register():
    return register_user()

@main_bp.route("/login", methods=["POST"])
def login():
    return login_user()

@main_bp.route("/reset-password", methods=["POST"])
def reset_password():
    return send_reset_email()

# Home route
@main_bp.route("/")
def home():
    return {"message": "Welcome to the Leave Management System"}

# Notifications route
@notifications_bp.route("/notifications", methods=["GET"])
def get_notifications():
    return {"message": "Notifications endpoint"}
