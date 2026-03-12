"""
routes/hospitals.py - Hospital CRUD and search APIs
"""
import random
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from bson import ObjectId

from database import get_db
from middleware.auth import token_required, admin_required

hospitals_bp = Blueprint("hospitals", __name__)


def _serialize_hospital(h):
    """Convert MongoDB document to JSON-serializable dict."""
    return {
        "id": str(h["_id"]),
        "hospital_name": h.get("hospital_name", ""),
        "location": h.get("location", ""),
        "address": h.get("address", ""),
        "total_beds": h.get("total_beds", 0),
        "emergency_available": h.get("emergency_available", False),
        "specialties": h.get("specialties", []),
        "phone": h.get("phone", ""),
        "email": h.get("email", ""),
        "rating": h.get("rating", 4.0),
        "image_url": h.get("image_url", ""),
        "crowd_data": h.get("crowd_data", {
            "current_waiting": random.randint(5, 45),
            "estimated_wait_minutes": random.randint(10, 90),
            "occupancy_percent": random.randint(30, 95),
        }),
        "created_at": h.get("created_at", datetime.now(timezone.utc)).isoformat(),
    }


@hospitals_bp.route("", methods=["POST"])
@admin_required
def add_hospital():
    """Add a new hospital (admin only)."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body required"}), 400

    hospital_name = data.get("hospital_name", "").strip()
    location = data.get("location", "").strip()
    address = data.get("address", "").strip()
    total_beds = data.get("total_beds", 0)

    if not all([hospital_name, location, address]):
        return jsonify({"success": False, "message": "hospital_name, location, and address are required"}), 400

    try:
        total_beds = int(total_beds)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "total_beds must be a number"}), 400

    db = get_db()

    hospital_doc = {
        "hospital_name": hospital_name,
        "location": location.lower(),
        "location_display": location,
        "address": address,
        "total_beds": total_beds,
        "emergency_available": bool(data.get("emergency_available", False)),
        "specialties": data.get("specialties", []),
        "phone": data.get("phone", ""),
        "email": data.get("email", ""),
        "rating": float(data.get("rating", 4.0)),
        "image_url": data.get("image_url", ""),
        "crowd_data": {
            "current_waiting": 0,
            "estimated_wait_minutes": 15,
            "occupancy_percent": 0,
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": request.current_user.get("user_id"),
    }

    result = db.hospitals.insert_one(hospital_doc)
    hospital_doc["_id"] = result.inserted_id

    return jsonify({
        "success": True,
        "message": "Hospital added successfully",
        "hospital": _serialize_hospital(hospital_doc),
    }), 201


@hospitals_bp.route("", methods=["GET"])
def get_hospitals():
    """Get all hospitals with optional search."""
    db = get_db()
    search = request.args.get("search", "").strip().lower()
    limit = min(int(request.args.get("limit", 20)), 100)
    skip = int(request.args.get("skip", 0))

    query = {}
    if search:
        query = {
            "$or": [
                {"location": {"$regex": search, "$options": "i"}},
                {"hospital_name": {"$regex": search, "$options": "i"}},
                {"address": {"$regex": search, "$options": "i"}},
            ]
        }

    hospitals = list(db.hospitals.find(query).skip(skip).limit(limit).sort("hospital_name", 1))
    total = db.hospitals.count_documents(query)

    return jsonify({
        "success": True,
        "hospitals": [_serialize_hospital(h) for h in hospitals],
        "total": total,
        "limit": limit,
        "skip": skip,
    }), 200


@hospitals_bp.route("/location", methods=["GET"])
def get_hospitals_by_location():
    """Search hospitals by location."""
    location = request.args.get("location", "").strip()
    if not location:
        return jsonify({"success": False, "message": "location parameter required"}), 400

    db = get_db()
    hospitals = list(db.hospitals.find({
        "$or": [
            {"location": {"$regex": location, "$options": "i"}},
            {"address": {"$regex": location, "$options": "i"}},
        ]
    }).limit(20))

    return jsonify({
        "success": True,
        "hospitals": [_serialize_hospital(h) for h in hospitals],
        "total": len(hospitals),
    }), 200


@hospitals_bp.route("/<hospital_id>", methods=["GET"])
def get_hospital(hospital_id):
    """Get single hospital details."""
    try:
        oid = ObjectId(hospital_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid hospital ID"}), 400

    db = get_db()
    hospital = db.hospitals.find_one({"_id": oid})
    if not hospital:
        return jsonify({"success": False, "message": "Hospital not found"}), 404

    # Get doctors for this hospital
    doctors = list(db.doctors.find({"hospital_id": hospital_id}).limit(20))
    doctors_list = [{
        "id": str(d["_id"]),
        "doctor_name": d.get("doctor_name", ""),
        "specialization": d.get("specialization", ""),
        "experience": d.get("experience", 0),
        "availability": d.get("availability", True),
        "schedule": d.get("schedule", "Mon-Sat 9AM-5PM"),
    } for d in doctors]

    result = _serialize_hospital(hospital)
    result["doctors"] = doctors_list

    return jsonify({"success": True, "hospital": result}), 200


@hospitals_bp.route("/<hospital_id>", methods=["PUT"])
@admin_required
def update_hospital(hospital_id):
    """Update hospital details (admin only)."""
    try:
        oid = ObjectId(hospital_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid hospital ID"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body required"}), 400

    db = get_db()
    allowed_fields = ["hospital_name", "location", "address", "total_beds",
                      "emergency_available", "specialties", "phone", "email", "rating"]

    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    if "location" in update_data:
        update_data["location_display"] = update_data["location"]
        update_data["location"] = update_data["location"].lower()
    update_data["updated_at"] = datetime.now(timezone.utc)

    result = db.hospitals.update_one({"_id": oid}, {"$set": update_data})
    if result.matched_count == 0:
        return jsonify({"success": False, "message": "Hospital not found"}), 404

    hospital = db.hospitals.find_one({"_id": oid})
    return jsonify({
        "success": True,
        "message": "Hospital updated successfully",
        "hospital": _serialize_hospital(hospital),
    }), 200


@hospitals_bp.route("/<hospital_id>/crowd", methods=["PUT"])
@admin_required
def update_crowd_data(hospital_id):
    """Update crowd monitoring data (admin only)."""
    try:
        oid = ObjectId(hospital_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid hospital ID"}), 400

    data = request.get_json()
    crowd_data = {
        "current_waiting": int(data.get("current_waiting", 0)),
        "estimated_wait_minutes": int(data.get("estimated_wait_minutes", 15)),
        "occupancy_percent": int(data.get("occupancy_percent", 0)),
    }

    db = get_db()
    result = db.hospitals.update_one({"_id": oid}, {"$set": {"crowd_data": crowd_data, "updated_at": datetime.now(timezone.utc)}})
    if result.matched_count == 0:
        return jsonify({"success": False, "message": "Hospital not found"}), 404

    return jsonify({"success": True, "message": "Crowd data updated", "crowd_data": crowd_data}), 200


@hospitals_bp.route("/<hospital_id>", methods=["DELETE"])
@admin_required
def delete_hospital(hospital_id):
    """Delete a hospital (admin only)."""
    try:
        oid = ObjectId(hospital_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid hospital ID"}), 400

    db = get_db()
    result = db.hospitals.delete_one({"_id": oid})
    if result.deleted_count == 0:
        return jsonify({"success": False, "message": "Hospital not found"}), 404

    return jsonify({"success": True, "message": "Hospital deleted successfully"}), 200
