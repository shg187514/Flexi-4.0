import os
import sys
import webbrowser

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from models import init_db

dist_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dist"))

app = Flask(__name__, static_folder=dist_folder if os.path.exists(dist_folder) else None, static_url_path="")
CORS(app, resources={r"/api/*": {"origins": "*"}})

init_db()

from routes.attendance import attendance_bp
from routes.faculty import faculty_bp
from routes.posttest import posttest_bp
from routes.pretest import pretest_bp
from routes.department import department_bp
from routes.trainee import trainee_bp
from routes.trainee_management import trainee_mgmt_bp
from routes.report import report_bp
from routes.dashboard import dashboard_bp
from routes.batch import batch_bp

app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
app.register_blueprint(faculty_bp, url_prefix="/api/faculty")
app.register_blueprint(posttest_bp, url_prefix="/api/posttest")
app.register_blueprint(pretest_bp, url_prefix="/api/pretest")
app.register_blueprint(department_bp, url_prefix="/api/department")
app.register_blueprint(trainee_bp, url_prefix="/api/trainees")
app.register_blueprint(trainee_mgmt_bp, url_prefix="/api/trainee-mgmt")
app.register_blueprint(report_bp, url_prefix="/api/reports")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(batch_bp, url_prefix="/api/batches")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve(path):
    if app.static_folder and os.path.exists(app.static_folder):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        index_path = os.path.join(app.static_folder, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(app.static_folder, "index.html")
    return jsonify({"message": "Flexi Training System API running"}), 200

@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    if os.environ.get("OPEN_BROWSER", "true").lower() in ("true", "1", "yes"):
        import time
        import threading
        def open_browser():
            time.sleep(1)
            try:
                webbrowser.open(f"http://localhost:{port}")
            except Exception:
                pass
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        app.run(debug=False, host="0.0.0.0", port=port)
    except OSError as e:
        if "already in use" in str(e).lower():
            print(f"Flexi Training server is already running on port {port}. Opening browser at http://localhost:{port}")
            try:
                webbrowser.open(f"http://localhost:{port}")
            except Exception:
                pass
        else:
            raise e
