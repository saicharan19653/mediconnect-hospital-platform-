"""
middleware/auth.py - JWT Authentication and Role-Based Access Control
"""
import os
import jwt
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timezone


def get_jwt_secret():
    return os.getenv("JWT_SECRET", "fallback_secret_change_in_production")


def decode_token(token):
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired. Please log in again."
    except jwt.InvalidTokenError as e:
        return None, f"Invalid token: {str(e)}"


def token_required(f):
    """Decorator: requires valid JWT token in Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Authorization token missing or malformed"}), 401

        token = auth_header.split(" ")[1]
        payload, error = decode_token(token)
        if error:
            return jsonify({"success": False, "message": error}), 401

        request.current_user = payload
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator: requires valid JWT token with admin role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Authorization token missing"}), 401

        token = auth_header.split(" ")[1]
        payload, error = decode_token(token)
        if error:
            return jsonify({"success": False, "message": error}), 401

        if payload.get("role") != "admin":
            return jsonify({"success": False, "message": "Admin access required"}), 403

        request.current_user = payload
        return f(*args, **kwargs)
    return decorated


def patient_required(f):
    """Decorator: requires valid JWT token with patient role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Authorization token missing"}), 401

        token = auth_header.split(" ")[1]
        payload, error = decode_token(token)
        if error:
            return jsonify({"success": False, "message": error}), 401

        if payload.get("role") != "patient":
            return jsonify({"success": False, "message": "Patient access required"}), 403

        request.current_user = payload
        return f(*args, **kwargs)
    return decorated
