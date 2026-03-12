"""
app.py - Hospital Services Platform - Main Flask Application
"""
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder="../frontend", static_url_path="/")
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.hospitals import hospitals_bp
    from routes.doctors import doctors_bp
    from routes.appointments import appointments_bp
    from routes.blood_donors import blood_donors_bp

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(hospitals_bp, url_prefix="/api/hospitals")
    app.register_blueprint(doctors_bp, url_prefix="/api/doctors")
    app.register_blueprint(appointments_bp, url_prefix="/api/appointments")
    app.register_blueprint(blood_donors_bp, url_prefix="/api/blood-donors")

    # Health check
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "message": "Hospital Platform API is running"}), 200

    # Serve frontend
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
        if path and os.path.exists(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, "pages/login.html")

    # Global error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "message": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"success": False, "message": "Internal server error"}), 500

    # Initialize DB on first request
    @app.before_request
    def init_db():
        from database import get_db
        try:
            get_db()
        except Exception as e:
            pass  # Will fail gracefully per route

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    print(f"🏥 Hospital Platform API starting on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
