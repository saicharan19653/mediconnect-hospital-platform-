"""
seed.py - Populate MongoDB with demo hospitals, doctors, and users
Run: python seed.py
"""
import os
import bcrypt
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/hospital_platform")

def get_db_name(uri):
    try:
        parts = uri.split("/")
        db_part = parts[-1].split("?")[0]
        return db_part if db_part else "hospital_platform"
    except:
        return "hospital_platform"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[get_db_name(MONGO_URI)]

print("🌱 Seeding database...")

# Clear existing data
db.users.drop()
db.hospitals.drop()
db.doctors.drop()
db.appointments.drop()
db.blood_donors.drop()
print("✓ Cleared existing data")

# ============================================================
# Users
# ============================================================
admin_pw = bcrypt.hashpw("Admin@123".encode(), bcrypt.gensalt())
patient_pw = bcrypt.hashpw("Patient@123".encode(), bcrypt.gensalt())

users_result = db.users.insert_many([
    {"name": "Admin User", "email": "admin@mediconnect.com", "password": admin_pw, "role": "admin", "created_at": datetime.now(timezone.utc)},
    {"name": "Priya Sharma", "email": "patient@mediconnect.com", "password": patient_pw, "role": "patient", "created_at": datetime.now(timezone.utc)},
    {"name": "Rajan Patel", "email": "rajan@example.com", "password": patient_pw, "role": "patient", "created_at": datetime.now(timezone.utc)},
])
user_ids = users_result.inserted_ids
print(f"✓ Created {len(user_ids)} users")

# ============================================================
# Hospitals
# ============================================================
hospitals_data = [
    {
        "hospital_name": "Apollo Hospitals",
        "location": "chennai", "location_display": "Chennai",
        "address": "21 Greams Road, Thousand Lights, Chennai - 600006",
        "total_beds": 550, "emergency_available": True,
        "specialties": ["Cardiology", "Neurology", "Oncology", "Transplant"],
        "phone": "+91 44 2829 0200", "email": "info@apollochennai.com",
        "rating": 4.8,
        "crowd_data": {"current_waiting": 23, "estimated_wait_minutes": 35, "occupancy_percent": 72},
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
    },
    {
        "hospital_name": "MIOT International",
        "location": "chennai", "location_display": "Chennai",
        "address": "4/112 Mount Poonamallee Rd, Manapakkam, Chennai - 600089",
        "total_beds": 1000, "emergency_available": True,
        "specialties": ["Orthopedics", "Spine Surgery", "Joint Replacement", "Rheumatology"],
        "phone": "+91 44 4200 2288", "email": "care@miotinternational.com",
        "rating": 4.7,
        "crowd_data": {"current_waiting": 15, "estimated_wait_minutes": 20, "occupancy_percent": 58},
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
    },
    {
        "hospital_name": "Fortis Malar Hospital",
        "location": "chennai", "location_display": "Chennai",
        "address": "52 1st Main Rd, Gandhi Nagar, Adyar, Chennai - 600020",
        "total_beds": 180, "emergency_available": True,
        "specialties": ["Cardiac Sciences", "Pediatrics", "Gastroenterology", "Urology"],
        "phone": "+91 44 4289 2222", "email": "fortismalar@fortishealthcare.com",
        "rating": 4.6,
        "crowd_data": {"current_waiting": 8, "estimated_wait_minutes": 15, "occupancy_percent": 45},
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
    },
    {
        "hospital_name": "Nandyala General Hospital",
        "location": "nandyal", "location_display": "Nandyal",
        "address": "Old Town, Nandyal, Andhra Pradesh - 518501",
        "total_beds": 200, "emergency_available": True,
        "specialties": ["General Medicine", "Surgery", "Pediatrics", "Gynecology"],
        "phone": "+91 8514 242424", "email": "nandyalhospital@ap.gov.in",
        "rating": 4.1,
        "crowd_data": {"current_waiting": 12, "estimated_wait_minutes": 25, "occupancy_percent": 61},
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
    },
    {
        "hospital_name": "Kurnool Government Medical College",
        "location": "kurnool", "location_display": "Kurnool",
        "address": "Hospital Rd, Kurnool, Andhra Pradesh - 518002",
        "total_beds": 1000, "emergency_available": True,
        "specialties": ["General Medicine", "Surgery", "Orthopedics", "Neurology", "Cardiology"],
        "phone": "+91 8518 244900", "email": "kurnoolhospital@ap.gov.in",
        "rating": 4.0,
        "crowd_data": {"current_waiting": 45, "estimated_wait_minutes": 80, "occupancy_percent": 88},
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
    },
    {
        "hospital_name": "Max Super Speciality Hospital",
        "location": "delhi", "location_display": "Delhi",
        "address": "1 2 Press Enclave Marg, Saket, New Delhi - 110017",
        "total_beds": 500, "emergency_available": True,
        "specialties": ["Cardiology", "Oncology", "Neurosciences", "Robotic Surgery"],
        "phone": "+91 11 2651 5050", "email": "saket@maxhealthcare.com",
        "rating": 4.7,
        "crowd_data": {"current_waiting": 31, "estimated_wait_minutes": 50, "occupancy_percent": 79},
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
    },
]
hosp_result = db.hospitals.insert_many(hospitals_data)
hosp_ids = hosp_result.inserted_ids
print(f"✓ Created {len(hosp_ids)} hospitals")

# ============================================================
# Doctors
# ============================================================
doctors_data = [
    {"doctor_name": "Rajesh Kumar", "specialization": "Cardiologist", "hospital_id": str(hosp_ids[0]), "hospital_name": "Apollo Hospitals", "experience": 18, "availability": True, "schedule": "Mon-Sat 9AM-2PM", "consultation_fee": 800, "qualification": "MBBS, MD, DM – Cardiology, AIIMS Delhi", "created_at": datetime.now(timezone.utc)},
    {"doctor_name": "Priya Venkatesh", "specialization": "Neurologist", "hospital_id": str(hosp_ids[0]), "hospital_name": "Apollo Hospitals", "experience": 14, "availability": True, "schedule": "Mon-Fri 10AM-4PM", "consultation_fee": 900, "qualification": "MBBS, DM – Neurology, CMC Vellore", "created_at": datetime.now(timezone.utc)},
    {"doctor_name": "S. Annamalai", "specialization": "Oncologist", "hospital_id": str(hosp_ids[0]), "hospital_name": "Apollo Hospitals", "experience": 22, "availability": False, "schedule": "Tue-Thu 11AM-3PM", "consultation_fee": 1200, "qualification": "MBBS, MD, DM – Medical Oncology", "created_at": datetime.now(timezone.utc)},
    {"doctor_name": "Meena Krishnaswamy", "specialization": "Orthopedic Surgeon", "hospital_id": str(hosp_ids[1]), "hospital_name": "MIOT International", "experience": 20, "availability": True, "schedule": "Mon-Sat 8AM-1PM", "consultation_fee": 700, "qualification": "MBBS, MS – Orthopedics, JIPMER", "created_at": datetime.now(timezone.utc)},
    {"doctor_name": "Arvind Balasubramanian", "specialization": "Spine Surgeon", "hospital_id": str(hosp_ids[1]), "hospital_name": "MIOT International", "experience": 16, "availability": True, "schedule": "Mon-Fri 9AM-5PM", "consultation_fee": 1000, "qualification": "MBBS, MS, MCh – Spine Surgery", "created_at": datetime.now(timezone.utc)},
    {"doctor_name": "Kavitha Rajan", "specialization": "Pediatrician", "hospital_id": str(hosp_ids[2]), "hospital_name": "Fortis Malar Hospital", "experience": 12, "availability": True, "schedule": "Mon-Sat 9AM-6PM", "consultation_fee": 600, "qualification": "MBBS, MD – Pediatrics, Madras Medical College", "created_at": datetime.now(timezone.utc)},
    {"doctor_name": "Suresh Babu", "specialization": "General Physician", "hospital_id": str(hosp_ids[3]), "hospital_name": "Nandyala General Hospital", "experience": 10, "availability": True, "schedule": "Mon-Sat 9AM-5PM", "consultation_fee": 200, "qualification": "MBBS, MD – General Medicine", "created_at": datetime.now(timezone.utc)},
    {"doctor_name": "Lakshmi Devi", "specialization": "Gynecologist", "hospital_id": str(hosp_ids[3]), "hospital_name": "Nandyala General Hospital", "experience": 15, "availability": True, "schedule": "Mon-Fri 10AM-4PM", "consultation_fee": 300, "qualification": "MBBS, MS – Obstetrics & Gynecology", "created_at": datetime.now(timezone.utc)},
    {"doctor_name": "Ramakrishna Reddy", "specialization": "Cardiologist", "hospital_id": str(hosp_ids[4]), "hospital_name": "Kurnool GMC", "experience": 25, "availability": True, "schedule": "Mon-Sat 8AM-2PM", "consultation_fee": 0, "qualification": "MBBS, DM – Cardiology, Government Service", "created_at": datetime.now(timezone.utc)},
    {"doctor_name": "Vijayalakshmi Sharma", "specialization": "Dermatologist", "hospital_id": str(hosp_ids[5]), "hospital_name": "Max Super Speciality", "experience": 11, "availability": True, "schedule": "Tue-Sat 10AM-5PM", "consultation_fee": 750, "qualification": "MBBS, MD – Dermatology, Lady Hardinge Medical College", "created_at": datetime.now(timezone.utc)},
]
doc_result = db.doctors.insert_many(doctors_data)
print(f"✓ Created {len(doc_result.inserted_ids)} doctors")

# ============================================================
# Blood Donors
# ============================================================
donors_data = [
    {"name": "Akash Singh", "blood_group": "O+", "location": "Chennai", "location_lower": "chennai", "phone": "+91 9876543210", "email": "akash@example.com", "availability": True, "last_donated": "2024-08-15", "age": 28, "registered_by": str(user_ids[1]), "created_at": datetime.now(timezone.utc)},
    {"name": "Sunita Rao", "blood_group": "A+", "location": "Nandyal", "location_lower": "nandyal", "phone": "+91 9876543211", "email": "sunita@example.com", "availability": True, "last_donated": "2024-09-20", "age": 35, "registered_by": str(user_ids[1]), "created_at": datetime.now(timezone.utc)},
    {"name": "Mohammed Ibrahim", "blood_group": "B+", "location": "Kurnool", "location_lower": "kurnool", "phone": "+91 9876543212", "email": "ibrahim@example.com", "availability": True, "last_donated": "", "age": 22, "registered_by": str(user_ids[2]), "created_at": datetime.now(timezone.utc)},
    {"name": "Geeta Patel", "blood_group": "AB+", "location": "Delhi", "location_lower": "delhi", "phone": "+91 9876543213", "email": "geeta@example.com", "availability": False, "last_donated": "2024-06-10", "age": 45, "registered_by": str(user_ids[2]), "created_at": datetime.now(timezone.utc)},
    {"name": "Ravi Kumar", "blood_group": "O-", "location": "Chennai", "location_lower": "chennai", "phone": "+91 9876543214", "email": "ravi@example.com", "availability": True, "last_donated": "2024-10-05", "age": 31, "registered_by": str(user_ids[1]), "created_at": datetime.now(timezone.utc)},
    {"name": "Ananya Reddy", "blood_group": "B-", "location": "Nandyal", "location_lower": "nandyal", "phone": "+91 9876543215", "email": "ananya@example.com", "availability": True, "last_donated": "", "age": 26, "registered_by": str(user_ids[2]), "created_at": datetime.now(timezone.utc)},
]
donor_result = db.blood_donors.insert_many(donors_data)
print(f"✓ Created {len(donor_result.inserted_ids)} blood donors")

print("\n" + "="*50)
print("✅ Seeding complete!")
print("="*50)
print(f"Admin Email:   admin@mediconnect.com")
print(f"Admin Password: Admin@123")
print(f"Patient Email:  patient@mediconnect.com")
print(f"Patient Password: Patient@123")
print("="*50)
client.close()
