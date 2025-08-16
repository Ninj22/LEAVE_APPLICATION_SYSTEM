from flask import Blueprint, redirect, url_for

main_bp = Blueprint("main", __name__)
notifications_bp = Blueprint("notifications", __name__)

@main_bp.route("/")
def home():
    return {"message": "Welcome to the Leave Management System"}

@main_bp.route("/register", methods=["POST"])
def register():
    return redirect(url_for("auth.signup"))

@main_bp.route("/login", methods=["POST"])
def login():
    return redirect(url_for("auth.login"))

@main_bp.route("/reset-password", methods=["POST"])
def reset_password():
    return redirect(url_for("auth.forgot_password"))

@notifications_bp.route("/notifications", methods=["GET"])
def get_notifications():
    return {"message": "Notifications endpoint"}