"""
routes/auth.py - User registration, login, and profile APIs
"""
import os
import re
import jwt
import bcrypt
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
from bson import ObjectId

from database import get_db

auth_bp = Blueprint("auth", __name__)


def _validate_email(email):
    return re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email) is not None


def _generate_token(user_id, email, role, name):
    payload = {
        "user_id": str(user_id),
        "email": email,
        "role": role,
        "name": name,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, os.getenv("JWT_SECRET", "fallback_secret"), algorithm="HS256")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user (patient or admin)."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body is required"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "patient").lower()

    # Validation
    if not all([name, email, password]):
        return jsonify({"success": False, "message": "Name, email, and password are required"}), 400
    if len(name) < 2:
        return jsonify({"success": False, "message": "Name must be at least 2 characters"}), 400
    if not _validate_email(email):
        return jsonify({"success": False, "message": "Invalid email format"}), 400
    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400
    if role not in ["admin", "patient"]:
        return jsonify({"success": False, "message": "Role must be 'admin' or 'patient'"}), 400

    db = get_db()

    # Check duplicate email
    if db.users.find_one({"email": email}):
        return jsonify({"success": False, "message": "Email already registered"}), 409

    # Hash password
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user_doc = {
        "name": name,
        "email": email,
        "password": hashed_pw,
        "role": role,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    result = db.users.insert_one(user_doc)
    token = _generate_token(result.inserted_id, email, role, name)

    return jsonify({
        "success": True,
        "message": "Registration successful",
        "token": token,
        "user": {"id": str(result.inserted_id), "name": name, "email": email, "role": role},
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body is required"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400

    db = get_db()
    user = db.users.find_one({"email": email})

    if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    token = _generate_token(user["_id"], user["email"], user["role"], user["name"])

    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        },
    }), 200


@auth_bp.route("/me", methods=["GET"])
def get_profile():
    """Get current user profile (requires token)."""
    from middleware.auth import decode_token
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"success": False, "message": "Token required"}), 401

    token = auth_header.split(" ")[1]
    payload, error = decode_token(token)
    if error:
        return jsonify({"success": False, "message": error}), 401

    db = get_db()
    user = db.users.find_one({"_id": ObjectId(payload["user_id"])})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    return jsonify({
        "success": True,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "created_at": user.get("created_at", "").isoformat() if user.get("created_at") else "",
        },
    }), 200
