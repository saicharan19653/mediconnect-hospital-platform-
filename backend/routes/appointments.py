"""
routes/appointments.py - Appointment booking and management APIs
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from bson import ObjectId

from database import get_db
from middleware.auth import token_required, admin_required

appointments_bp = Blueprint("appointments", __name__)


def _serialize_appointment(a):
    return {
        "id": str(a["_id"]),
        "patient_id": a.get("patient_id", ""),
        "patient_name": a.get("patient_name", ""),
        "patient_email": a.get("patient_email", ""),
        "doctor_id": a.get("doctor_id", ""),
        "doctor_name": a.get("doctor_name", ""),
        "hospital_id": a.get("hospital_id", ""),
        "hospital_name": a.get("hospital_name", ""),
        "date": a.get("date", ""),
        "time": a.get("time", ""),
        "status": a.get("status", "pending"),
        "notes": a.get("notes", ""),
        "specialization": a.get("specialization", ""),
        "created_at": a.get("created_at", datetime.now(timezone.utc)).isoformat(),
    }


@appointments_bp.route("", methods=["POST"])
@token_required
def book_appointment():
    """Book a new appointment (authenticated users)."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body required"}), 400

    doctor_id = data.get("doctor_id", "").strip()
    hospital_id = data.get("hospital_id", "").strip()
    date = data.get("date", "").strip()
    time = data.get("time", "").strip()

    if not all([doctor_id, hospital_id, date, time]):
        return jsonify({"success": False, "message": "doctor_id, hospital_id, date, and time are required"}), 400

    # Validate date format
    try:
        appt_date = datetime.strptime(date, "%Y-%m-%d")
        if appt_date.date() < datetime.now(timezone.utc).date():
            return jsonify({"success": False, "message": "Appointment date cannot be in the past"}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Date must be in YYYY-MM-DD format"}), 400

    db = get_db()

    # Get doctor info
    try:
        doctor = db.doctors.find_one({"_id": ObjectId(doctor_id)})
    except Exception:
        return jsonify({"success": False, "message": "Invalid doctor_id"}), 400

    if not doctor:
        return jsonify({"success": False, "message": "Doctor not found"}), 404
    if not doctor.get("availability", True):
        return jsonify({"success": False, "message": "Doctor is not available"}), 400

    # Get hospital info
    try:
        hospital = db.hospitals.find_one({"_id": ObjectId(hospital_id)})
    except Exception:
        return jsonify({"success": False, "message": "Invalid hospital_id"}), 400

    if not hospital:
        return jsonify({"success": False, "message": "Hospital not found"}), 404

    # Check slot availability (max 10 appointments per doctor per time slot)
    existing = db.appointments.count_documents({
        "doctor_id": doctor_id,
        "date": date,
        "time": time,
        "status": {"$ne": "cancelled"},
    })
    if existing >= 10:
        return jsonify({"success": False, "message": "This time slot is fully booked. Please choose another time."}), 409

    current_user = request.current_user
    appointment_doc = {
        "patient_id": current_user["user_id"],
        "patient_name": current_user.get("name", ""),
        "patient_email": current_user.get("email", ""),
        "doctor_id": doctor_id,
        "doctor_name": doctor.get("doctor_name", ""),
        "specialization": doctor.get("specialization", ""),
        "hospital_id": hospital_id,
        "hospital_name": hospital.get("hospital_name", ""),
        "date": date,
        "time": time,
        "status": "pending",
        "notes": data.get("notes", ""),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    result = db.appointments.insert_one(appointment_doc)
    appointment_doc["_id"] = result.inserted_id

    return jsonify({
        "success": True,
        "message": "Appointment booked successfully",
        "appointment": _serialize_appointment(appointment_doc),
    }), 201


@appointments_bp.route("", methods=["GET"])
@token_required
def get_appointments():
    """Get appointments. Admins see all; patients see their own."""
    current_user = request.current_user
    db = get_db()

    limit = min(int(request.args.get("limit", 50)), 200)
    skip = int(request.args.get("skip", 0))
    status = request.args.get("status", "").strip()

    if current_user["role"] == "admin":
        query = {}
    else:
        query = {"patient_id": current_user["user_id"]}

    if status:
        query["status"] = status

    appointments = list(db.appointments.find(query)
                        .sort("created_at", -1)
                        .skip(skip)
                        .limit(limit))
    total = db.appointments.count_documents(query)

    return jsonify({
        "success": True,
        "appointments": [_serialize_appointment(a) for a in appointments],
        "total": total,
    }), 200


@appointments_bp.route("/<appointment_id>", methods=["GET"])
@token_required
def get_appointment(appointment_id):
    """Get single appointment."""
    try:
        oid = ObjectId(appointment_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid appointment ID"}), 400

    db = get_db()
    appointment = db.appointments.find_one({"_id": oid})
    if not appointment:
        return jsonify({"success": False, "message": "Appointment not found"}), 404

    current_user = request.current_user
    if current_user["role"] != "admin" and appointment["patient_id"] != current_user["user_id"]:
        return jsonify({"success": False, "message": "Access denied"}), 403

    return jsonify({"success": True, "appointment": _serialize_appointment(appointment)}), 200


@appointments_bp.route("/<appointment_id>/status", methods=["PUT"])
@token_required
def update_appointment_status(appointment_id):
    """Update appointment status."""
    try:
        oid = ObjectId(appointment_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid appointment ID"}), 400

    data = request.get_json()
    new_status = data.get("status", "").strip().lower()
    valid_statuses = ["pending", "confirmed", "completed", "cancelled"]

    if new_status not in valid_statuses:
        return jsonify({"success": False, "message": f"Status must be one of: {', '.join(valid_statuses)}"}), 400

    db = get_db()
    appointment = db.appointments.find_one({"_id": oid})
    if not appointment:
        return jsonify({"success": False, "message": "Appointment not found"}), 404

    current_user = request.current_user
    # Patients can only cancel their own appointments
    if current_user["role"] != "admin":
        if appointment["patient_id"] != current_user["user_id"]:
            return jsonify({"success": False, "message": "Access denied"}), 403
        if new_status not in ["cancelled"]:
            return jsonify({"success": False, "message": "Patients can only cancel appointments"}), 403

    db.appointments.update_one({"_id": oid}, {
        "$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}
    })

    return jsonify({"success": True, "message": f"Appointment {new_status} successfully"}), 200
