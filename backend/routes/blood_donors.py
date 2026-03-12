"""
routes/blood_donors.py - Blood donor registration and search APIs
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from bson import ObjectId

from database import get_db
from middleware.auth import token_required, admin_required

blood_donors_bp = Blueprint("blood_donors", __name__)

VALID_BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


def _serialize_donor(d):
    return {
        "id": str(d["_id"]),
        "name": d.get("name", ""),
        "blood_group": d.get("blood_group", ""),
        "location": d.get("location", ""),
        "phone": d.get("phone", ""),
        "email": d.get("email", ""),
        "availability": d.get("availability", True),
        "last_donated": d.get("last_donated", ""),
        "age": d.get("age", None),
        "registered_by": d.get("registered_by", ""),
        "created_at": d.get("created_at", datetime.now(timezone.utc)).isoformat(),
    }


@blood_donors_bp.route("", methods=["POST"])
@token_required
def register_donor():
    """Register as a blood donor."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Request body required"}), 400

    name = data.get("name", "").strip()
    blood_group = data.get("blood_group", "").strip().upper()
    location = data.get("location", "").strip()
    phone = data.get("phone", "").strip()

    if not all([name, blood_group, location, phone]):
        return jsonify({"success": False, "message": "name, blood_group, location, and phone are required"}), 400

    if blood_group not in VALID_BLOOD_GROUPS:
        return jsonify({"success": False, "message": f"blood_group must be one of: {', '.join(VALID_BLOOD_GROUPS)}"}), 400

    db = get_db()
    current_user = request.current_user

    donor_doc = {
        "name": name,
        "blood_group": blood_group,
        "location": location,
        "location_lower": location.lower(),
        "phone": phone,
        "email": data.get("email", current_user.get("email", "")),
        "availability": bool(data.get("availability", True)),
        "last_donated": data.get("last_donated", ""),
        "age": int(data.get("age")) if data.get("age") else None,
        "registered_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    result = db.blood_donors.insert_one(donor_doc)
    donor_doc["_id"] = result.inserted_id

    return jsonify({
        "success": True,
        "message": "Blood donor registered successfully",
        "donor": _serialize_donor(donor_doc),
    }), 201


@blood_donors_bp.route("", methods=["GET"])
def get_donors():
    """Search blood donors by blood group and/or location."""
    db = get_db()
    blood_group = request.args.get("blood_group", "").strip().upper()
    location = request.args.get("location", "").strip()
    availability = request.args.get("availability", "").strip()
    limit = min(int(request.args.get("limit", 50)), 200)
    skip = int(request.args.get("skip", 0))

    query = {}
    if blood_group:
        if blood_group not in VALID_BLOOD_GROUPS:
            return jsonify({"success": False, "message": f"Invalid blood group. Valid: {', '.join(VALID_BLOOD_GROUPS)}"}), 400
        query["blood_group"] = blood_group
    if location:
        query["location_lower"] = {"$regex": location.lower(), "$options": "i"}
    if availability.lower() == "true":
        query["availability"] = True

    donors = list(db.blood_donors.find(query).skip(skip).limit(limit).sort("created_at", -1))
    total = db.blood_donors.count_documents(query)

    return jsonify({
        "success": True,
        "donors": [_serialize_donor(d) for d in donors],
        "total": total,
    }), 200


@blood_donors_bp.route("/<donor_id>", methods=["PUT"])
@token_required
def update_donor(donor_id):
    """Update donor info (own record or admin)."""
    try:
        oid = ObjectId(donor_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid donor ID"}), 400

    db = get_db()
    donor = db.blood_donors.find_one({"_id": oid})
    if not donor:
        return jsonify({"success": False, "message": "Donor not found"}), 404

    current_user = request.current_user
    if current_user["role"] != "admin" and donor["registered_by"] != current_user["user_id"]:
        return jsonify({"success": False, "message": "Access denied"}), 403

    data = request.get_json()
    allowed = ["name", "location", "phone", "email", "availability", "last_donated", "age"]
    update_data = {k: v for k, v in data.items() if k in allowed}
    if "location" in update_data:
        update_data["location_lower"] = update_data["location"].lower()
    update_data["updated_at"] = datetime.now(timezone.utc)

    db.blood_donors.update_one({"_id": oid}, {"$set": update_data})
    donor = db.blood_donors.find_one({"_id": oid})

    return jsonify({
        "success": True,
        "message": "Donor updated successfully",
        "donor": _serialize_donor(donor),
    }), 200


@blood_donors_bp.route("/<donor_id>", methods=["DELETE"])
@token_required
def delete_donor(donor_id):
    """Delete donor record."""
    try:
        oid = ObjectId(donor_id)
    except Exception:
        return jsonify({"success": False, "message": "Invalid donor ID"}), 400

    db = get_db()
    donor = db.blood_donors.find_one({"_id": oid})
    if not donor:
        return jsonify({"success": False, "message": "Donor not found"}), 404

    current_user = request.current_user
    if current_user["role"] != "admin" and donor["registered_by"] != current_user["user_id"]:
        return jsonify({"success": False, "message": "Access denied"}), 403

    db.blood_donors.delete_one({"_id": oid})
    return jsonify({"success": True, "message": "Donor removed successfully"}), 200
