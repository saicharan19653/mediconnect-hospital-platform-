import os
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

_client = None
_db = None

def get_db():
    global _client, _db
    if _db is None:
        mongo_uri = "mongodb+srv://stylesense:style12345@cluster0.uxleewd.mongodb.net/hospital_platform?retryWrites=true&w=majority&appName=Cluster0"
        try:
            _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            _client.admin.command('ping')
            _db = _client["hospital_platform"]
            _create_indexes(_db)
            print("✅ Connected to MongoDB Atlas successfully")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise
    return _db

def _create_indexes(db):
    try:
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.hospitals.create_index([("location", ASCENDING)])
        db.doctors.create_index([("hospital_id", ASCENDING)])
        db.appointments.create_index([("patient_id", ASCENDING)])
        db.blood_donors.create_index([("blood_group", ASCENDING)])
        print("✅ MongoDB indexes created")
    except Exception as e:
        print(f"⚠️ Index warning: {e}")

def close_db():
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None