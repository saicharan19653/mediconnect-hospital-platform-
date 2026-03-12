# 🏥 MediConnect — Hospital Services Platform

A full-stack web application for hospital services: find hospitals, book appointments, manage doctors, and register as blood donors.

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, Vanilla JavaScript |
| Backend | Python 3.10+, Flask 3.0 |
| Database | MongoDB Atlas (or local MongoDB) |
| Auth | JWT + bcrypt |

---

## 📁 Project Structure

```
hospital-platform/
├── backend/
│   ├── app.py                    # Flask application entry point
│   ├── database.py               # MongoDB connection + index setup
│   ├── seed.py                   # Demo data seeder
│   ├── requirements.txt
│   ├── .env.example              # Environment variable template
│   ├── middleware/
│   │   └── auth.py               # JWT middleware & role decorators
│   └── routes/
│       ├── auth.py               # /api/register, /api/login, /api/me
│       ├── hospitals.py          # /api/hospitals
│       ├── doctors.py            # /api/doctors
│       ├── appointments.py       # /api/appointments
│       └── blood_donors.py       # /api/blood-donors
└── frontend/
    ├── index.html                # Root redirect
    ├── css/
    │   └── main.css              # Complete stylesheet
    ├── js/
    │   └── api.js                # API client, Auth, UI helpers
    └── pages/
        ├── login.html
        ├── register.html
        ├── patient-dashboard.html
        ├── hospitals.html
        ├── doctors.html
        ├── appointment-booking.html
        ├── blood-donation.html
        ├── admin-dashboard.html
        ├── add-hospital.html
        ├── add-doctor.html
        └── manage-appointments.html
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- MongoDB Atlas account (free tier works) or local MongoDB
- pip

### 1. Clone/Extract the project

```bash
cd hospital-platform
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# OR: venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your MongoDB connection:

```env
# MongoDB Atlas URI (get from Atlas dashboard → Connect → Drivers)
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/hospital_platform?retryWrites=true&w=majority

# JWT Secret (use a long random string in production)
JWT_SECRET=your_super_secret_jwt_key_change_me_to_something_long_and_random

FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
```

### 4. Seed Demo Data

```bash
python seed.py
```

Output:
```
✅ Seeding complete!
Admin Email:    admin@mediconnect.com
Admin Password: Admin@123
Patient Email:  patient@mediconnect.com
Patient Password: Patient@123
```

### 5. Start the Server

```bash
python app.py
```

Open: **http://localhost:5000**

---

## 🔑 Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Administrator | admin@mediconnect.com | Admin@123 |
| Patient | patient@mediconnect.com | Patient@123 |

---

## 🌐 API Reference

### Authentication
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/register` | ❌ | Register new user |
| POST | `/api/login` | ❌ | Login & get JWT |
| GET | `/api/me` | ✅ | Get current user |

### Hospitals
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/hospitals` | ❌ | List/search hospitals |
| GET | `/api/hospitals/location?location=<city>` | ❌ | Filter by location |
| GET | `/api/hospitals/<id>` | ❌ | Get hospital + doctors |
| POST | `/api/hospitals` | 🔑 Admin | Add hospital |
| PUT | `/api/hospitals/<id>` | 🔑 Admin | Update hospital |
| DELETE | `/api/hospitals/<id>` | 🔑 Admin | Delete hospital |
| PUT | `/api/hospitals/<id>/crowd` | 🔑 Admin | Update crowd data |

### Doctors
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/doctors` | ❌ | List doctors (filterable) |
| GET | `/api/doctors/<id>` | ❌ | Get doctor details |
| POST | `/api/doctors` | 🔑 Admin | Add doctor |
| PUT | `/api/doctors/<id>` | 🔑 Admin | Update doctor |
| DELETE | `/api/doctors/<id>` | 🔑 Admin | Delete doctor |

### Appointments
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/appointments` | ✅ | Get appointments (role-filtered) |
| POST | `/api/appointments` | ✅ | Book appointment |
| GET | `/api/appointments/<id>` | ✅ | Get single appointment |
| PUT | `/api/appointments/<id>/status` | ✅ | Update status |

### Blood Donors
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/blood-donors` | ❌ | Search donors |
| POST | `/api/blood-donors` | ✅ | Register as donor |
| PUT | `/api/blood-donors/<id>` | ✅ | Update donor info |
| DELETE | `/api/blood-donors/<id>` | ✅ | Remove donor |

---

## 🔒 Security Features

- **JWT authentication** with 7-day expiry
- **bcrypt password hashing** (salt rounds auto-generated)
- **Role-based access control** via middleware decorators
- **Input validation** on all endpoints
- **MongoDB injection prevention** via pymongo's parameterized queries
- **CORS** restricted to `/api/*` routes

---

## ✨ Innovation Feature: Hospital Crowd Monitoring

Each hospital displays real-time crowd statistics:
- **Current waiting patients** count
- **Estimated wait time** in minutes  
- **Bed occupancy percentage** with color-coded progress bar
  - 🟢 Green: <50% — Low wait
  - 🟡 Amber: 50-80% — Moderate
  - 🔴 Red: >80% — High congestion

Admins can update these values in real-time via the dashboard.

---

## 🗃️ MongoDB Collections Schema

### users
```json
{ "name": "string", "email": "string (unique)", "password": "hashed", "role": "admin|patient" }
```

### hospitals
```json
{ "hospital_name": "string", "location": "string (lowercase)", "address": "string",
  "total_beds": "int", "emergency_available": "bool", "specialties": ["array"],
  "crowd_data": { "current_waiting": 0, "estimated_wait_minutes": 15, "occupancy_percent": 0 } }
```

### doctors
```json
{ "doctor_name": "string", "specialization": "string", "hospital_id": "string",
  "experience": "int", "availability": "bool", "schedule": "string", "consultation_fee": "float" }
```

### appointments
```json
{ "patient_id": "string", "doctor_id": "string", "hospital_id": "string",
  "date": "YYYY-MM-DD", "time": "string", "status": "pending|confirmed|completed|cancelled", "notes": "string" }
```

### blood_donors
```json
{ "name": "string", "blood_group": "A+|A-|B+|B-|AB+|AB-|O+|O-",
  "location": "string", "phone": "string", "availability": "bool" }
```

---

## 🚀 Production Deployment Notes

1. Set `FLASK_DEBUG=False` and `FLASK_ENV=production`
2. Use a strong, random `JWT_SECRET` (min 32 chars)
3. Enable MongoDB Atlas IP whitelist for your server IP
4. Add HTTPS (nginx + certbot)
5. Use gunicorn: `gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()`

---

## 📄 License

MIT License — Free to use and modify.
