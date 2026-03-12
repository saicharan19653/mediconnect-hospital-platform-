"""
routes/doctors.py - Doctor management APIs
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from bson import ObjectId

from database import get_db
from middleware.auth import token_required, admin_required

doctors_bp = Blueprint("doctors", __name__)


def _serialize_doctor(d, hospital_name=""):
    return {
        "id": str(d["_id"]),
        "doctor_name": d.get("doctor_name", ""),
        "specialization": d.get("specialization", ""),
        "hospital_id": d.get("hospital_id", ""),
        "hospital_name": hospital_name or d.get("hospital_name", ""),
        "experience": d.get("experience", 0),
        "availability": d.get("availability", True),
        "schedule": d.get("schedule", "Mon-Sat 9AM-5PM"),
        "consultation_fee": d.get("consultation_fee", 0),
        "qualification": d.get("qualification", ""),
        "bio": d.get("bio", ""),
        "created_at": d.get("created_at", datetime.now(timezone.utc)).isoformat(),
    }


@doctors_bp.route("", methods=["POST"])
@admin_required
def add_doctor():
    """Add a new doctor (admin only)."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body required"}), 400

    doctor_name = data.get("doctor_name", "").strip()
    specialization = data.get("specialization", "").strip()
    hospital_id = data.get("hospital_id", "").strip()
    experience = data.get("experience", 0)

    if not all([doctor_name, specialization, hospital_id]):
        return jsonify({"success": False, "message": "doctor_name, specialization, and hospital_id are required"}), 400

    db = get_db()

    # Verify hospital exists
    try:
        hosp = db.hospitals.find_one({"_id": ObjectId(hospital_id)})
    except Exception:
        return jsonify({"success": False, "message": "Invalid hospital_id"}), 400

    if not hosp:
        return jsonify({"success": False, "message": "Hospital not found"}), 404

    doctor_doc = {
        "doctor_name": doctor_name,
        "specialization": specialization,
        "hospital_id": hospital_id,
        "hospital_name": hosp.get("hospital_name", ""),
        "experience": int(experience),
        "availability": bool(data.get("availability", True)),
        "schedule": data.get("schedule", "Mon-Sat 9AM-5PM"),
        "consultation_fee": float(data.get("consultation_fee", 0)),
        "qualification": data.get("qualification", ""),
        "bio": data.get("bio", ""),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    result = db.doctors.insert_one(doctor_doc)
    doctor_doc["_id"] = result.inserted_id

    return jsonify({
        "success": True,
        "message": "Doctor added successfully",
        "doctor": _serialize_doctor(doctor_doc),
    }), 201


@doctors_bp.route("", methods=["GET"])
def get_doctors():
    """Get all doctors with optional filters."""
    db = get_db()
    hospital_id = request.args.get("hospital_id", "").strip()
    specialization = request.args.get("specialization", "").strip()
    availability = request.args.get("availability", "").strip()
    limit = min(int(request.args.get("limit", 50)), 100)
    skip = int(request.args.get("skip", 0))

    query = {}
    if hospital_id:
        query["hospital_id"] = hospital_id
    if specialization:
        query["specialization"] = {"$regex": specialization, "$options": "i"}
    if availability.lower() == "true":
        query["availability"] = True
    elif availability.lower() == "false":
        query["availability"] = False

    doctors = list(db.doctors.find(query).skip(skip).limit(limit).sort("doctor_name", 1))
    total = db.doctors.count_documents(query)

    return jsonify({
        "success": True,
        "doctors": [_serialize_doctor(d) for d in doctors],
        "total": total,
    }), 200


@doctors_bp.route("/<doctor_id>", methods=["GET"])
def get_doctor(doctor_id):
    """Get single doctor details."""
    try:
        oid = ObjectId(doctor_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid doctor ID"}), 400

    db = get_db()
    doctor = db.doctors.find_one({"_id": oid})
    if not doctor:
        return jsonify({"success": False, "message": "Doctor not found"}), 404

    return jsonify({"success": True, "doctor": _serialize_doctor(doctor)}), 200


@doctors_bp.route("/<doctor_id>", methods=["PUT"])
@admin_required
def update_doctor(doctor_id):
    """Update doctor details (admin only)."""
    try:
        oid = ObjectId(doctor_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid doctor ID"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body required"}), 400

    db = get_db()
    allowed = ["doctor_name", "specialization", "experience", "availability",
               "schedule", "consultation_fee", "qualification", "bio"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    update_data["updated_at"] = datetime.now(timezone.utc)

    result = db.doctors.update_one({"_id": oid}, {"$set": update_data})
    if result.matched_count == 0:
        return jsonify({"success": False, "message": "Doctor not found"}), 404

    doctor = db.doctors.find_one({"_id": oid})
    return jsonify({
        "success": True,
        "message": "Doctor updated successfully",
        "doctor": _serialize_doctor(doctor),
    }), 200


@doctors_bp.route("/<doctor_id>", methods=["DELETE"])
@admin_required
def delete_doctor(doctor_id):
    """Delete a doctor (admin only)."""
    try:
        oid = ObjectId(doctor_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid doctor ID"}), 400

    db = get_db()
    result = db.doctors.delete_one({"_id": oid})
    if result.deleted_count == 0:
        return jsonify({"success": False, "message": "Doctor not found"}), 404

    return jsonify({"success": True, "message": "Doctor deleted successfully"}), 200
